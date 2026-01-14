import sys, os, math
import numpy as np
import sounddevice as sd
import librosa

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QSlider, QStyle,
    QFrame, QGroupBox, QGridLayout
)
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QLinearGradient, QBrush, QPen
from PyQt5.QtCore import QThread, Qt, QTimer, pyqtSignal


# ================= AUDIO THREAD =================
class AudioThread(QThread):
    position_changed = pyqtSignal(float)  # Emits current position in seconds
    loading_complete = pyqtSignal(str)    # Emits when loading is complete
    loading_started = pyqtSignal(str)     # Emits when loading starts
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.current_position = 0.0  # Current position in seconds
        self.angle = 0.0
        self.duration = 0.0
        self.force_seek = None  # Force seek to this position

        self.visual_samples = np.zeros(256, dtype=np.float32)

    def load(self, file):
        """Load audio file"""
        self.loading_started.emit(os.path.basename(file))
        
        try:
            # Load audio file
            y, self.sr = librosa.load(file, mono=True, sr=22050)
            y = y / max(np.max(np.abs(y)), 1e-6)
            self.mono = y.astype(np.float32)
            self.current_position = 0.0
            self.angle = 0.0
            self.duration = len(y) / self.sr
            self.position_changed.emit(0.0)
            self.loading_complete.emit(os.path.basename(file))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def seek(self, position):
        """Force seek to position in seconds"""
        if self.mono is not None:
            # Clamp position to valid range
            position = max(0.0, min(position, self.duration))
            print(f"AudioThread: Seeking to {position:.2f} seconds")
            self.force_seek = position
            self.current_position = position

    def callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)
        
        # Handle force seek
        if self.force_seek is not None:
            self.current_position = self.force_seek
            self.force_seek = None
            print(f"Callback: Starting from {self.current_position:.2f}s")
        
        # Calculate starting sample
        start_sample = int(self.current_position * self.sr)
        
        # Check bounds
        if start_sample >= len(self.mono):
            outdata[:] = np.zeros((frames, 2), np.float32)
            self.running = False
            return
        
        for i in range(frames):
            if start_sample + i >= len(self.mono):
                # End of track
                self.running = False
                break

            base = self.mono[start_sample + i] * self.volume
            self.visual_samples[i % 256] = base

            pan = (math.sin(self.angle) + 1) * 0.5
            self.angle += 0.0006

            L = R = base

            if self.effect == "Rock":
                L *= 1.35
                R *= 1.35

            elif self.effect == "3D":
                L = base * (1 - pan) * 1.3
                R = base * pan * 1.3

            elif self.effect == "8D":
                depth = 1.0 - abs(math.cos(self.angle)) * 0.3
                L = base * (1 - pan) * depth * 1.4
                R = base * pan * depth * 1.4

            elif self.effect == "Dolby":
                side = math.sin(self.angle) * 0.3
                bass = base * 0.3
                L = base + side + bass
                R = base - side + bass

            out[i, 0] = np.tanh(L)
            out[i, 1] = np.tanh(R)
        
        # Update current position
        frames_processed = min(frames, len(self.mono) - start_sample)
        self.current_position += frames_processed / self.sr
        
        # Emit position update
        self.position_changed.emit(self.current_position)

        outdata[:] = out

    def run(self):
        self.running = True
        with sd.OutputStream(
            samplerate=self.sr,
            channels=2,
            callback=self.callback,
            blocksize=1024
        ):
            while self.running:
                sd.sleep(30)

    def stop(self):
        self.running = False


# ================= SPECTRUM VISUALIZER =================
class Spectrum(QWidget):
    def __init__(self, audio):
        super().__init__()
        self.audio = audio
        self.mode = "Bars"
        self.phase = 0.0
        self.setMinimumHeight(280)

    def set_mode(self, mode):
        self.mode = mode
        self.update()

    def paintEvent(self, e):
        if self.audio.visual_samples is None:
            return

        data = np.abs(np.fft.rfft(self.audio.visual_samples))[:64]

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if self.mode == "Bars":
            bw = w / len(data)
            for i, v in enumerate(data):
                bh = min(v * 40, h)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    int(i * bw),
                    h - int(bh),
                    int(bw - 2),
                    int(bh)
                )

        elif self.mode == "Wave":
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            
            self.phase += 0.04
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                painter.setBrush(QColor.fromHsv((i * 6) % 360, 255, 255))
                painter.drawEllipse(x - 3, y - 3, 6, 6)

        elif self.mode == "Circle":
            radius = min(cx, cy) - 30
            for i, v in enumerate(data):
                angle = (i / len(data)) * 2 * math.pi
                r = radius + v * 25
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x), int(y), 6, 6)


# ================= SIMPLE MUSIC PLAYER =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Professional DJ Music Player")
        self.resize(1200, 700)
        
        # Simple dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton {
                background-color: #2d2d2d;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
            QPushButton:pressed {
                background-color: #1d1d1d;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #00b4d8;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 20px;
                margin: -6px 0;
                border-radius: 10px;
                border: 2px solid #00b4d8;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                selection-background-color: #00b4d8;
                border: none;
                font-size: 12px;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 4px;
            }
            QLabel {
                font-size: 12px;
            }
        """)

        self.audio = AudioThread()
        self.files = []
        self.current_file_index = -1
        self.user_is_seeking = False  # Flag to track if user is dragging slider

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.audio.position_changed.connect(self.update_progress_from_audio)
        self.audio.loading_started.connect(self.show_loading)
        self.audio.loading_complete.connect(self.hide_loading)

        # Timer for visualizer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        
        self.title_label = QLabel("🎧 No Track Playing")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #00b4d8;")
        
        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #ff9900;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addWidget(self.loading_label)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # ===== LEFT PANEL - Playlist =====
        left_panel = QVBoxLayout()
        
        playlist_label = QLabel("Playlist")
        playlist_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #00b4d8;")
        left_panel.addWidget(playlist_label)
        
        self.table = QTableWidget(0, 1)
        self.table.setHorizontalHeaderLabels(["Track"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnWidth(0, 280)
        self.table.cellDoubleClicked.connect(self.play_selected)
        left_panel.addWidget(self.table)
        
        # Simple buttons
        btn_layout = QHBoxLayout()
        load_btn = QPushButton("📁 Load Folder")
        load_btn.clicked.connect(self.load_folder)
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        
        btn_layout.addWidget(load_btn)
        btn_layout.addWidget(clear_btn)
        left_panel.addLayout(btn_layout)
        
        content_layout.addLayout(left_panel, 1)

        # ===== RIGHT PANEL =====
        right_panel = QVBoxLayout()
        
        # Visualizer
        self.spectrum = Spectrum(self.audio)
        self.spectrum.setMinimumHeight(250)
        right_panel.addWidget(self.spectrum)
        
        # Visualizer mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Visual Mode:"))
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        mode_layout.addWidget(self.spectrum_mode)
        mode_layout.addStretch()
        right_panel.addLayout(mode_layout)

        # ===== PROGRESS BAR SECTION =====
        progress_frame = QFrame()
        progress_frame.setStyleSheet("background-color: #1e1e1e; border-radius: 5px; padding: 10px;")
        progress_layout = QVBoxLayout(progress_frame)
        
        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("font-weight: bold;")
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("font-weight: bold;")
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.duration_label)
        progress_layout.addLayout(time_layout)
        
        # SINGLE PROGRESS BAR
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 10000)  # Higher resolution for smooth seeking
        self.progress_bar.setValue(0)
        
        # Connect progress bar signals
        self.progress_bar.sliderPressed.connect(self.start_seeking)
        self.progress_bar.sliderReleased.connect(self.end_seeking)
        self.progress_bar.sliderMoved.connect(self.update_seek_preview)
        
        progress_layout.addWidget(self.progress_bar)
        right_panel.addWidget(progress_frame)

        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

        # ===== CONTROL PANEL =====
        control_panel = QHBoxLayout()
        
        # Transport controls
        transport_layout = QHBoxLayout()
        
        def create_btn(text, tooltip=""):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(50, 50)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 25px;
                    background-color: #222;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #333;
                }
            """)
            return btn
        
        self.btn_prev = create_btn("⏮", "Previous")
        self.btn_play = create_btn("▶", "Play/Pause")
        self.btn_next = create_btn("⏭", "Next")
        self.btn_stop = create_btn("⏹", "Stop")
        
        self.btn_prev.clicked.connect(self.prev)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_next.clicked.connect(self.next)
        self.btn_stop.clicked.connect(self.stop)
        
        transport_layout.addWidget(self.btn_prev)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_next)
        transport_layout.addWidget(self.btn_stop)
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(lambda v: setattr(self.audio, 'volume', v/100))
        self.volume_slider.setFixedWidth(100)
        volume_layout.addWidget(self.volume_slider)
        
        # Effects
        effects_layout = QHBoxLayout()
        effects_layout.addWidget(QLabel("FX:"))
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects_combo.currentTextChanged.connect(lambda e: setattr(self.audio, 'effect', e))
        self.effects_combo.setFixedWidth(100)
        effects_layout.addWidget(self.effects_combo)
        
        control_panel.addLayout(transport_layout)
        control_panel.addStretch()
        control_panel.addLayout(volume_layout)
        control_panel.addLayout(effects_layout)
        
        main_layout.addLayout(control_panel)

    def show_loading(self, filename):
        self.loading_label.setText(f"Loading: {filename}...")
        self.loading_label.setVisible(True)

    def hide_loading(self, filename):
        self.loading_label.setText("")
        self.loading_label.setVisible(False)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        self.files.clear()
        self.table.setRowCount(0)

        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
                file_path = os.path.join(folder, f)
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(f))
                self.files.append(file_path)

    def clear_playlist(self):
        self.files.clear()
        self.table.setRowCount(0)
        self.stop()

    def play_selected(self, row=None):
        if row is None:
            row = self.table.currentRow()
        
        if 0 <= row < len(self.files):
            self.current_file_index = row
            file_path = self.files[row]
            
            if self.audio.load(file_path):
                self.title_label.setText(f"🎧 {os.path.basename(file_path)}")
                
                if not self.audio.isRunning():
                    self.audio.start()
                
                self.audio.running = True
                self.btn_play.setText("⏸")
                
                # Update duration display
                mins = int(self.audio.duration // 60)
                secs = int(self.audio.duration % 60)
                self.duration_label.setText(f"{mins:02d}:{secs:02d}")
                
                # Reset progress
                self.progress_bar.setValue(0)

    def toggle_play(self):
        if self.audio.mono is None and self.files:
            self.play_selected(0)
        elif self.audio.mono is not None:
            self.audio.running = not self.audio.running
            if self.audio.running:
                self.btn_play.setText("⏸")
            else:
                self.btn_play.setText("▶")

    def stop(self):
        self.audio.running = False
        self.btn_play.setText("▶")
        self.progress_bar.setValue(0)
        self.current_time_label.setText("00:00")

    def next(self):
        if not self.files:
            return
        next_index = (self.current_file_index + 1) % len(self.files)
        self.table.selectRow(next_index)
        self.play_selected(next_index)

    def prev(self):
        if not self.files:
            return
        prev_index = (self.current_file_index - 1) % len(self.files)
        self.table.selectRow(prev_index)
        self.play_selected(prev_index)

    # ===== SIMPLE SEEKING LOGIC =====
    def start_seeking(self):
        """User started dragging the progress bar"""
        self.user_is_seeking = True
        print("User started seeking")

    def update_seek_preview(self, value):
        """Update time display while user is dragging"""
        if self.audio.mono is not None and self.audio.duration > 0:
            # Calculate time from progress bar value
            position = (value / 10000.0) * self.audio.duration
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def end_seeking(self):
        """User released the progress bar - perform seek"""
        if self.audio.mono is not None and self.audio.duration > 0:
            # Calculate the time to seek to
            value = self.progress_bar.value()
            position = (value / 10000.0) * self.audio.duration
            
            print(f"Seeking to position: {position:.2f} seconds")
            
            # Perform the seek
            self.audio.seek(position)
            
            # Update time display
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            # Ensure audio is playing
            if not self.audio.running:
                self.audio.running = True
                self.btn_play.setText("⏸")
            
            self.user_is_seeking = False

    def update_progress_from_audio(self, position):
        """Update progress bar from audio thread (when not seeking)"""
        if not self.user_is_seeking and self.audio.mono is not None and self.audio.duration > 0:
            # Calculate progress bar value from position
            value = int((position / self.audio.duration) * 10000)
            self.progress_bar.setValue(value)
            
            # Update time display
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            # Auto-next when song ends
            if position >= self.audio.duration - 0.5:
                self.next()

    def update_visualizer(self):
        self.spectrum.update()

    def closeEvent(self, e):
        self.audio.stop()
        if self.audio.isRunning():
            self.audio.terminate()
            self.audio.wait()
        e.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    w = MusicPlayer()
    w.show()
    
    sys.exit(app.exec_())