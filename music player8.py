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
    loading_complete = pyqtSignal(str)  # Emits when loading is complete
    loading_started = pyqtSignal(str)  # Emits when loading starts
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.current_time = 0.0
        self.angle = 0.0
        self.duration = 0.0
        self.seek_requested = None  # Store seek position request
        self.seek_sample = 0  # Sample index to seek to

        self.visual_samples = np.zeros(256, dtype=np.float32)

    def load(self, file):
        """Load audio file with better performance"""
        self.loading_started.emit(os.path.basename(file))
        
        try:
            # Use lower sampling rate for faster loading
            y, self.sr = librosa.load(file, mono=True, sr=22050)
            y = y / max(np.max(np.abs(y)), 1e-6)
            self.mono = y.astype(np.float32)
            self.current_time = 0.0
            self.angle = 0.0
            self.duration = len(y) / self.sr
            self.seek_sample = 0
            self.position_changed.emit(0.0)
            self.loading_complete.emit(os.path.basename(file))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def seek(self, position):
        """Seek to position in seconds"""
        if self.mono is not None:
            self.seek_requested = position
            self.seek_sample = int(position * self.sr)
            # Clamp to valid range
            self.seek_sample = max(0, min(self.seek_sample, len(self.mono) - 1))
            self.current_time = self.seek_sample / self.sr
            self.position_changed.emit(self.current_time)

    def callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)
        
        # Start from seek position if requested
        if self.seek_requested is not None:
            current_sample = self.seek_sample
            self.seek_requested = None
        else:
            current_sample = int(self.current_time * self.sr)
        
        for i in range(frames):
            if current_sample + i >= len(self.mono):
                # End of track
                out[i:] = np.zeros((frames - i, 2), np.float32)
                self.running = False
                break

            base = self.mono[current_sample + i] * self.volume
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

        # Update current time
        if self.seek_requested is None:
            self.current_time += frames / self.sr
            self.position_changed.emit(self.current_time)

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

        # FFT for visualization - KEEP ORIGINAL SETTINGS
        data = np.abs(np.fft.rfft(self.audio.visual_samples))[:64]

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if self.mode == "Bars":
            # KEEP ORIGINAL BAR STYLE
            bw = w / len(data)
            for i, v in enumerate(data):
                # Original bar height calculation
                bh = min(v * 40, h)
                
                # Original color scheme from first version
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                
                # Original bar drawing - simple solid color bars
                x = int(i * bw)
                painter.drawRect(
                    int(i * bw),
                    h - int(bh),
                    int(bw - 2),  # Original spacing
                    int(bh)
                )

        elif self.mode == "Wave":
            # Enhanced wave visualization
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            
            self.phase += 0.04
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                
                # Draw circle at each point
                painter.setBrush(QColor.fromHsv((i * 6) % 360, 255, 255))
                painter.drawEllipse(x - 3, y - 3, 6, 6)

        elif self.mode == "Circle":
            # Enhanced circle visualization
            radius = min(cx, cy) - 30
            for i, v in enumerate(data):
                angle = (i / len(data)) * 2 * math.pi
                r = radius + v * 25
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                
                # Original circle style
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x), int(y), 6, 6)


# ================= MUSIC PLAYER UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Professional DJ Music Player")
        self.resize(1200, 700)
        
        # Apply dark theme with original bar colors
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
            QSlider::handle:horizontal:hover {
                background: #f0f0f0;
                border: 2px solid #00ccff;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                selection-background-color: #00b4d8;
                border: none;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 4px;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 10px;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00b4d8;
            }
            QLabel {
                font-size: 12px;
            }
        """)

        self.audio = AudioThread()
        self.files = []
        self.current_file_index = -1
        self.loading_label = None
        self.is_seeking = False
        self.seek_position = 0.0

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.audio.position_changed.connect(self.update_position)
        self.audio.loading_started.connect(self.show_loading)
        self.audio.loading_complete.connect(self.hide_loading)

        # Timer for UI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        
        self.title_label = QLabel("🎧 No Track Playing")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #00b4d8; padding: 5px;")
        
        # Loading indicator
        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #ff9900; font-style: italic;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addWidget(self.loading_label)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # ===== LEFT PANEL - Playlist =====
        left_panel = QVBoxLayout()
        
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QVBoxLayout()
        playlist_layout.setContentsMargins(5, 15, 5, 5)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Track", "Duration"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 70)
        self.table.cellDoubleClicked.connect(self.play_selected)
        
        playlist_layout.addWidget(self.table)
        
        # Playlist controls
        playlist_controls = QHBoxLayout()
        
        load_folder_btn = QPushButton("📁 Load Folder")
        load_folder_btn.clicked.connect(self.load_folder)
        load_folder_btn.setStyleSheet("""
            background-color: #00b4d8;
            padding: 6px 12px;
            border-radius: 3px;
        """)
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        clear_btn.setStyleSheet("padding: 6px 12px;")
        
        playlist_controls.addWidget(load_folder_btn)
        playlist_controls.addWidget(clear_btn)
        playlist_controls.addStretch()
        
        playlist_layout.addLayout(playlist_controls)
        playlist_group.setLayout(playlist_layout)
        left_panel.addWidget(playlist_group)
        
        content_layout.addLayout(left_panel, 1)

        # ===== RIGHT PANEL - Visualizer & Controls =====
        right_panel = QVBoxLayout()
        
        # Visualizer
        visualizer_group = QGroupBox("Visualizer")
        visualizer_layout = QVBoxLayout()
        visualizer_layout.setContentsMargins(5, 15, 5, 5)
        
        self.spectrum = Spectrum(self.audio)
        self.spectrum.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0a0f, stop:1 #050505);")
        visualizer_layout.addWidget(self.spectrum)
        
        # Visualizer mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Visual Mode:"))
        
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        self.spectrum_mode.setFixedWidth(120)
        mode_layout.addWidget(self.spectrum_mode)
        mode_layout.addStretch()
        
        visualizer_layout.addLayout(mode_layout)
        visualizer_group.setLayout(visualizer_layout)
        right_panel.addWidget(visualizer_group, 2)

        # Progress bar with better styling
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(5, 15, 5, 5)
        
        self.time_labels = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("font-weight: bold; color: #00b4d8;")
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("font-weight: bold;")
        self.time_labels.addWidget(self.current_time_label)
        self.time_labels.addStretch()
        self.time_labels.addWidget(QLabel("/"))
        self.time_labels.addWidget(self.total_time_label)
        progress_layout.addLayout(self.time_labels)
        
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.sliderPressed.connect(self.seek_start)
        self.progress.sliderReleased.connect(self.seek_end)
        self.progress.sliderMoved.connect(self.seek_move)
        self.progress.setTickPosition(QSlider.NoTicks)
        progress_layout.addWidget(self.progress)
        
        progress_group.setLayout(progress_layout)
        right_panel.addWidget(progress_group)

        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

        # ===== CONTROL PANEL =====
        control_panel = QHBoxLayout()
        
        # Transport controls
        transport_group = QGroupBox("Transport")
        transport_layout = QHBoxLayout()
        transport_layout.setContentsMargins(10, 15, 10, 10)
        
        # Create transport buttons with better styling
        def create_transport_button(symbol, tooltip=""):
            btn = QPushButton(symbol)
            btn.setToolTip(tooltip)
            btn.setFixedSize(56, 56)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 28px;
                    background-color: #222;
                    font-size: 24px;
                    font-weight: bold;
                    border: 2px solid #444;
                }
                QPushButton:hover {
                    background-color: #333;
                    border: 2px solid #00b4d8;
                }
                QPushButton:pressed {
                    background-color: #111;
                    border: 2px solid #0088aa;
                }
            """)
            return btn
        
        # Create buttons
        self.btn_prev = create_transport_button("⏮", "Previous Track")
        self.btn_prev.clicked.connect(self.prev)
        
        self.btn_play = create_transport_button("▶", "Play/Pause")
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_next = create_transport_button("⏭", "Next Track")
        self.btn_next.clicked.connect(self.next)
        
        self.btn_stop = create_transport_button("⏹", "Stop")
        self.btn_stop.clicked.connect(self.stop)
        
        transport_layout.addWidget(self.btn_prev)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_next)
        transport_layout.addWidget(self.btn_stop)
        transport_group.setLayout(transport_layout)
        
        control_panel.addWidget(transport_group)

        # Volume control
        volume_group = QGroupBox("Volume")
        volume_layout = QHBoxLayout()
        volume_layout.setContentsMargins(10, 15, 10, 10)
        
        # Volume icon that changes with level
        self.volume_icon = QLabel("🔊")
        self.volume_icon.setFixedWidth(30)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff3333, stop:0.5 #ffff33, stop:1 #33ff33);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 2px solid #444;
            }
        """)
        
        volume_layout.addWidget(self.volume_icon)
        volume_layout.addWidget(self.volume_slider)
        volume_group.setLayout(volume_layout)
        control_panel.addWidget(volume_group)

        # Effects
        effects_group = QGroupBox("Effects")
        effects_layout = QHBoxLayout()
        effects_layout.setContentsMargins(10, 15, 10, 10)
        
        effect_icon = QLabel("🎛️")
        effect_icon.setFixedWidth(30)
        
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects_combo.currentTextChanged.connect(self.set_effect)
        self.effects_combo.setFixedWidth(100)
        
        effects_layout.addWidget(effect_icon)
        effects_layout.addWidget(self.effects_combo)
        effects_group.setLayout(effects_layout)
        control_panel.addWidget(effects_group)

        control_panel.addStretch()
        main_layout.addLayout(control_panel)

    # ===== LOADING HANDLERS =====
    def show_loading(self, filename):
        self.loading_label.setText(f"Loading: {filename}...")
        self.loading_label.setVisible(True)
        QApplication.processEvents()

    def hide_loading(self, filename):
        self.loading_label.setText("")
        self.loading_label.setVisible(False)
        QApplication.processEvents()

    # ===== PLAYBACK CONTROL =====
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        self.files.clear()
        self.table.setRowCount(0)

        # Quick scan for audio files
        audio_files = []
        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
                audio_files.append(f)

        # Add files to table quickly
        for f in audio_files:
            file_path = os.path.join(folder, f)
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # Track name
            track_item = QTableWidgetItem(f)
            track_item.setData(Qt.UserRole, file_path)
            
            # Duration (will be calculated later)
            duration_item = QTableWidgetItem("--:--")
            
            self.table.setItem(r, 0, track_item)
            self.table.setItem(r, 1, duration_item)
            self.files.append(file_path)

        # Calculate durations in background
        self.calculate_durations()

    def calculate_durations(self):
        """Calculate durations for all files in background"""
        for row in range(self.table.rowCount()):
            file_path = self.files[row]
            try:
                # Quick duration calculation
                duration = librosa.get_duration(filename=file_path)
                mins = int(duration // 60)
                secs = int(duration % 60)
                duration_str = f"{mins:02d}:{secs:02d}"
                
                self.table.item(row, 1).setText(duration_str)
                QApplication.processEvents()
            except:
                pass

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
            
            # Stop current playback
            self.audio.running = False
            
            # Load and play
            def load_and_play():
                if self.audio.load(file_path):
                    self.title_label.setText(f"🎧 {os.path.basename(file_path)}")
                    
                    if not self.audio.isRunning():
                        self.audio.start()
                    
                    self.audio.running = True
                    self.btn_play.setText("⏸")  # Change to pause symbol
                    
                    # Update total time
                    duration = self.audio.duration
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    self.total_time_label.setText(f"{mins:02d}:{secs:02d}")
                    
                    # Reset progress bar
                    self.progress.setValue(0)
            
            # Start loading in background
            import threading
            threading.Thread(target=load_and_play, daemon=True).start()

    def toggle_play(self):
        if self.audio.mono is None and self.files:
            self.play_selected(0)
        elif self.audio.mono is not None:
            self.audio.running = not self.audio.running
            if self.audio.running:
                self.btn_play.setText("⏸")  # Pause symbol
            else:
                self.btn_play.setText("▶")  # Play symbol

    def stop(self):
        self.audio.running = False
        self.btn_play.setText("▶")
        self.progress.setValue(0)
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")

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

    # ===== FIXED SEEKING IMPLEMENTATION =====
    def seek_start(self):
        """User started dragging the progress bar"""
        self.is_seeking = True

    def seek_move(self, value):
        """User is dragging the progress bar"""
        if self.audio.mono is not None and self.audio.duration > 0:
            # Calculate position based on slider value (0-1000)
            position = (value / 1000.0) * self.audio.duration
            
            # Store for when user releases
            self.seek_position = position
            
            # Update time display immediately while dragging
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def seek_end(self):
        """User released the progress bar - jump to position"""
        if self.audio.mono is not None and self.audio.duration > 0 and self.is_seeking:
            print(f"Seeking to: {self.seek_position:.2f} seconds")
            
            # Perform the seek
            self.audio.seek(self.seek_position)
            
            # Update UI
            self.progress.setValue(int((self.seek_position / self.audio.duration) * 1000))
            
            # If audio was playing, keep it playing
            if not self.audio.running:
                self.audio.running = True
                self.btn_play.setText("⏸")
            
            self.is_seeking = False

    # ===== UI UPDATES =====
    def update_position(self, position):
        """Update progress bar and time display during normal playback"""
        if self.audio.mono is not None and self.audio.duration > 0 and not self.is_seeking:
            # Calculate progress value (0-1000)
            progress_value = int((position / self.audio.duration) * 1000)
            
            # Update progress bar
            self.progress.setValue(progress_value)
            
            # Update time display
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            # Check if track ended
            if position >= self.audio.duration - 0.1:  # Small buffer
                self.next()

    def update_visualizer(self):
        self.spectrum.update()

    def set_volume(self, value):
        self.audio.volume = value / 100.0
        # Update volume icon based on level
        if value == 0:
            self.volume_icon.setText("🔇")
        elif value < 33:
            self.volume_icon.setText("🔈")
        elif value < 66:
            self.volume_icon.setText("🔉")
        else:
            self.volume_icon.setText("🔊")

    def set_effect(self, effect):
        self.audio.effect = effect

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
    
    # Set application-wide font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    w = MusicPlayer()
    w.show()
    
    sys.exit(app.exec_())