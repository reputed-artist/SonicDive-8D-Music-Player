import sys, os, math
import numpy as np
import librosa
import sounddevice as sd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QFileDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QComboBox, QStackedWidget
)
from PyQt5.QtCore import Qt, QThread, QTimer
from PyQt5.QtGui import QPixmap, QIcon

import pyqtgraph as pg

# ================= AUDIO ENGINE =================
class AudioThread(QThread):
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Normal"
        self.mono = None
        self.sr = 44100
        self.idx = 0
        self.angle = 0.0

    def load(self, file):
        y, self.sr = librosa.load(file, mono=True)
        y = y / max(np.max(np.abs(y)), 1e-6)
        self.mono = y.astype(np.float32)
        self.idx = 0
        self.angle = 0.0

    def set_effect(self, fx):
        self.effect = fx

    def callback(self, outdata, frames, time, status):
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2))
            return

        out = np.zeros((frames, 2), dtype=np.float32)

        for i in range(frames):
            if self.idx >= len(self.mono):
                self.idx = 0

            base = float(self.mono[self.idx])
            pan = (math.sin(self.angle) + 1) * 0.5
            depth = 0.8 + 0.2 * math.cos(self.angle)

            if self.effect == "8D":
                out_l = base * (1 - pan) * depth * 1.35
                out_r = base * pan * depth * 1.35

            elif self.effect == "3D":
                out_l = base * (1 - pan) * 1.25
                out_r = base * pan * 1.25

            elif self.effect == "Dolby":
                mid = base * 1.1
                side = math.sin(self.angle) * 0.25
                bass = base * 0.2
                out_l = mid + side + bass
                out_r = mid - side + bass

            elif self.effect == "Rock":
                out_l = base * 1.35
                out_r = base * 1.35

            else:
                out_l = base
                out_r = base

            out[i, 0] = np.tanh(out_l)
            out[i, 1] = np.tanh(out_r)

            self.idx += 1
            self.angle += 0.002

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
                sd.sleep(50)

    def stop(self):
        self.running = False


# ================= MAIN UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ Spatial Music Player")
        self.setGeometry(300, 120, 900, 600)

        self.audio = AudioThread()
        self.files = []
        self.current = 0
        self.is_playing = False

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 🎵 Thumbnail
        self.thumb = QLabel("🎵")
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet("font-size:120px;")
        layout.addWidget(self.thumb)

        # 🎚 Controls
        controls = QHBoxLayout()

        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_next = QPushButton("⏭")
        self.btn_list = QPushButton("📃")
        self.btn_spec = QPushButton("📊")

        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_list.clicked.connect(self.toggle_playlist)
        self.btn_spec.clicked.connect(self.toggle_spectrum)

        for b in [self.btn_prev, self.btn_play, self.btn_next, self.btn_list, self.btn_spec]:
            b.setFixedSize(60, 40)
            controls.addWidget(b)

        layout.addLayout(controls)

        # 🎧 Effects
        self.effects = QComboBox()
        self.effects.addItems(["Normal", "3D", "8D", "Dolby", "Rock"])
        self.effects.currentTextChanged.connect(self.audio.set_effect)
        layout.addWidget(self.effects)

        # 📊 Spectrum
        self.spectrum = pg.PlotWidget()
        self.spectrum.hide()
        layout.addWidget(self.spectrum)

        # 📃 Playlist
        self.playlist = QListWidget()
        self.playlist.hide()
        self.playlist.itemDoubleClicked.connect(self.select_track)
        layout.addWidget(self.playlist)

        # 📂 Load Folder
        load_btn = QPushButton("📂 Load Music Folder")
        load_btn.clicked.connect(self.load_folder)
        layout.addWidget(load_btn)

        # Spectrum Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spectrum)
        self.timer.start(50)

    # ---------- Functions ----------
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return
        self.files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".mp3", ".wav"))
        ]
        self.playlist.clear()
        for f in self.files:
            self.playlist.addItem(os.path.basename(f))

    def toggle_play(self):
        if not self.files:
            return

        if not self.is_playing:
            self.audio.load(self.files[self.current])
            if not self.audio.isRunning():
                self.audio.start()
            self.audio.running = True
            self.btn_play.setText("⏸")
        else:
            self.audio.running = False
            self.btn_play.setText("▶")

        self.is_playing = not self.is_playing

    def select_track(self):
        self.current = self.playlist.currentRow()
        self.is_playing = False
        self.toggle_play()

    def next_track(self):
        if not self.files:
            return
        self.current = (self.current + 1) % len(self.files)
        self.is_playing = False
        self.toggle_play()

    def prev_track(self):
        if not self.files:
            return
        self.current = (self.current - 1) % len(self.files)
        self.is_playing = False
        self.toggle_play()

    def toggle_playlist(self):
        self.playlist.setVisible(not self.playlist.isVisible())

    def toggle_spectrum(self):
        self.spectrum.setVisible(not self.spectrum.isVisible())

    def update_spectrum(self):
        if self.audio.mono is None:
            return
        segment = self.audio.mono[self.audio.idx:self.audio.idx + 512]
        if len(segment) < 512:
            return
        fft = np.abs(np.fft.rfft(segment))
        self.spectrum.plot(fft, clear=True)

    def closeEvent(self, event):
        self.audio.stop()
        event.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MusicPlayer()
    win.show()
    sys.exit(app.exec_())
