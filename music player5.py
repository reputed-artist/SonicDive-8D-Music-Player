import sys, os, math
import numpy as np
import sounddevice as sd
import librosa

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QSlider, QStyle,
    QProgressBar, QFrame, QGroupBox, QGridLayout
)
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QLinearGradient, QBrush
from PyQt5.QtCore import QThread, Qt, QTimer, pyqtSignal


# ================= AUDIO THREAD =================
class AudioThread(QThread):
    position_changed = pyqtSignal(float)  # Emits current position in seconds
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8
        self.seek_position = None  # Position to seek to in seconds

        self.mono = None
        self.sr = 44100
        self.current_time = 0.0
        self.angle = 0.0
        self.duration = 0.0

        self.visual_samples = np.zeros(512, dtype=np.float32)

    def load(self, file):
        try:
            y, self.sr = librosa.load(file, mono=True, sr=None)
            y = y / max(np.max(np.abs(y)), 1e-6)
            self.mono = y.astype(np.float32)
            self.current_time = 0.0
            self.angle = 0.0
            self.duration = len(y) / self.sr
            self.position_changed.emit(0.0)
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def seek(self, position):
        """Seek to position in seconds"""
        if self.mono is not None:
            self.current_time = max(0, min(position, self.duration))
            sample_pos = int(self.current_time * self.sr)
            self.current_time = sample_pos / self.sr  # Ensure exact sample position

    def callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)
        
        # Calculate starting sample
        sample_pos = int(self.current_time * self.sr)
        
        for i in range(frames):
            if sample_pos + i >= len(self.mono):
                out[i:] = np.zeros((frames - i, 2), np.float32)
                self.running = False
                break

            base = self.mono[sample_pos + i] * self.volume
            self.visual_samples[i % 512] = base

            pan = (math.sin(self.angle) + 1) * 0.5
            self.angle += 0.0006

            L = R = base

            if self.effect == "Rock":
                # Distortion-like effect
                L *= 1.35
                R *= 1.35
                L = np.tanh(L * 1.5) * 0.8
                R = np.tanh(R * 1.5) * 0.8

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

            elif self.effect == "Echo":
                # Simple echo effect
                if i >= 5000:  # Add delay
                    L = base * 0.7 + out[i-5000, 0] * 0.3
                    R = base * 0.7 + out[i-5000, 1] * 0.3

            out[i, 0] = np.clip(L, -1.0, 1.0)
            out[i, 1] = np.clip(R, -1.0, 1.0)

        # Update current time
        self.current_time += frames / self.sr
        self.position_changed.emit(self.current_time)

        outdata[:] = out

    def run(self):
        self.running = True
        with sd.OutputStream(
            samplerate=self.sr,
            channels=2,
            callback=self.callback,
            blocksize=2048
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
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1a1a2e, stop:1 #0f0f23);")

    def set_mode(self, mode):
        self.mode = mode
        self.update()

    def paintEvent(self, e):
        if self.audio.visual_samples is None:
            return

        # FFT for visualization
        data = np.abs(np.fft.rfft(self.audio.visual_samples * np.hanning(len(self.audio.visual_samples))))[:128]
        data = np.log1p(data * 100)
        data = data / np.max(data) if np.max(data) > 0 else data

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if self.mode == "Bars":
            # Gradient background
            gradient = QLinearGradient(0, 0, 0, h)
            gradient.setColorAt(0, QColor(26, 26, 46, 200))
            gradient.setColorAt(1, QColor(15, 15, 35, 200))
            painter.fillRect(0, 0, w, h, gradient)

            # Draw bars with gradient
            bw = w / len(data)
            for i, v in enumerate(data):
                bh = v * h * 0.7
                color = QColor.fromHsv((i * 3) % 360, 200, 255)
                
                # Bar gradient
                bar_gradient = QLinearGradient(0, h - bh, 0, h)
                bar_gradient.setColorAt(0, color.lighter(150))
                bar_gradient.setColorAt(1, color.darker(150))
                
                painter.setBrush(QBrush(bar_gradient))
                painter.setPen(Qt.NoPen)
                
                x = int(i * bw)
                painter.drawRect(x, h - int(bh), int(bw - 1), int(bh))

        elif self.mode == "Wave":
            painter.setBrush(Qt.NoBrush)
            
            # Draw waveform
            points = []
            for i, v in enumerate(data):
                x = (i / len(data)) * w
                y = cy + math.sin(self.phase + i * 0.1) * v * 100
                points.append((x, y))

            self.phase += 0.02

            # Draw smooth curve
            painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        elif self.mode == "Circle":
            radius = min(cx, cy) - 20
            
            # Draw circular spectrum
            for i, v in enumerate(data):
                angle = (i / len(data)) * 2 * math.pi
                r = radius + v * 40
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                
                color = QColor.fromHsv((i * 3) % 360, 180, 255)
                painter.setBrush(color)
                painter.setPen(QColor(255, 255, 255, 100))
                painter.drawEllipse(int(x - 3), int(y - 3), 6, 6)


# ================= MUSIC PLAYER UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Professional DJ Music Player")
        self.setWindowIcon(QIcon.fromTheme("multimedia-player"))
        self.resize(1200, 700)
        
        # Apply dark theme
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
                height: 6px;
                background: #333;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00b4d8;
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                selection-background-color: #00b4d8;
                border: none;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 8px;
                border: none;
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
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        self.audio = AudioThread()
        self.files = []
        self.current_file_index = -1

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.audio.position_changed.connect(self.update_position)

        # Timer for UI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        
        self.title_label = QLabel("🎧 No Track Playing")
        self.title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #00b4d8;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # ===== LEFT PANEL - Playlist =====
        left_panel = QVBoxLayout()
        
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QVBoxLayout()
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Track", "Duration"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 80)
        self.table.cellDoubleClicked.connect(self.play_selected)
        
        playlist_layout.addWidget(self.table)
        
        # Playlist controls
        playlist_controls = QHBoxLayout()
        
        load_folder_btn = QPushButton("📁 Load Folder")
        load_folder_btn.clicked.connect(self.load_folder)
        load_folder_btn.setStyleSheet("background-color: #00b4d8;")
        
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_playlist)
        
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
        
        self.spectrum = Spectrum(self.audio)
        visualizer_layout.addWidget(self.spectrum)
        
        # Visualizer mode selector
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        mode_layout.addWidget(self.spectrum_mode)
        mode_layout.addStretch()
        
        visualizer_layout.addLayout(mode_layout)
        visualizer_group.setLayout(visualizer_layout)
        right_panel.addWidget(visualizer_group, 2)

        # Progress bar
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.time_labels = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.time_labels.addWidget(self.current_time_label)
        self.time_labels.addStretch()
        self.time_labels.addWidget(self.total_time_label)
        progress_layout.addLayout(self.time_labels)
        
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderPressed.connect(self.seek_start)
        self.progress.sliderReleased.connect(self.seek_end)
        self.progress.sliderMoved.connect(self.seek_move)
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
        
        style = self.style()
        
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(style.standardIcon(QStyle.SP_MediaSkipBackward))
        self.btn_prev.setFixedSize(50, 50)
        self.btn_prev.clicked.connect(self.prev)
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(style.standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.setFixedSize(60, 60)
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_next = QPushButton()
        self.btn_next.setIcon(style.standardIcon(QStyle.SP_MediaSkipForward))
        self.btn_next.setFixedSize(50, 50)
        self.btn_next.clicked.connect(self.next)
        
        self.btn_stop = QPushButton()
        self.btn_stop.setIcon(style.standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.setFixedSize(50, 50)
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
        volume_layout.addWidget(QLabel("🔊"))
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_slider.setFixedWidth(150)
        
        volume_layout.addWidget(self.volume_slider)
        volume_group.setLayout(volume_layout)
        control_panel.addWidget(volume_group)

        # Effects
        effects_group = QGroupBox("Effects")
        effects_layout = QHBoxLayout()
        effects_layout.addWidget(QLabel("FX:"))
        
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby", "Echo"])
        self.effects_combo.currentTextChanged.connect(self.set_effect)
        self.effects_combo.setFixedWidth(120)
        
        effects_layout.addWidget(self.effects_combo)
        effects_group.setLayout(effects_layout)
        control_panel.addWidget(effects_group)

        control_panel.addStretch()
        main_layout.addLayout(control_panel)

    # ===== PLAYBACK CONTROL =====
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        self.files.clear()
        self.table.setRowCount(0)

        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a")):
                file_path = os.path.join(folder, f)
                try:
                    # Get duration
                    y, sr = librosa.load(file_path, sr=None, mono=True, duration=0.1)
                    duration = len(y) / sr
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_str = f"{mins:02d}:{secs:02d}"
                except:
                    duration_str = "--:--"

                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(f))
                self.table.setItem(r, 1, QTableWidgetItem(duration_str))
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
                self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
                
                # Update total time
                duration = self.audio.duration
                mins = int(duration // 60)
                secs = int(duration % 60)
                self.total_time_label.setText(f"{mins:02d}:{secs:02d}")

    def toggle_play(self):
        if self.audio.mono is None and self.files:
            self.play_selected(0)
        elif self.audio.mono is not None:
            self.audio.running = not self.audio.running
            icon = QStyle.SP_MediaPause if self.audio.running else QStyle.SP_MediaPlay
            self.btn_play.setIcon(self.style().standardIcon(icon))

    def stop(self):
        self.audio.running = False
        if self.audio.isRunning():
            self.audio.terminate()
            self.audio.wait()
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.progress.setValue(0)
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

    # ===== SEEKING =====
    def seek_start(self):
        pass  # No special handling needed

    def seek_move(self, value):
        # Update time label during seek
        if self.audio.mono is not None:
            position = (value / 1000) * self.audio.duration
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def seek_end(self):
        if self.audio.mono is not None:
            position = (self.progress.value() / 1000) * self.audio.duration
            self.audio.seek(position)

    # ===== UI UPDATES =====
    def update_position(self, position):
        if self.audio.mono is not None:
            # Update progress bar
            progress_value = int((position / self.audio.duration) * 1000)
            self.progress.setValue(progress_value)
            
            # Update time label
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def update_visualizer(self):
        self.spectrum.update()

    def set_volume(self, value):
        self.audio.volume = value / 100

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
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    w = MusicPlayer()
    w.show()
    
    sys.exit(app.exec_())