import sys, os, math
import numpy as np
import sounddevice as sd
import librosa

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QSlider
)
from PyQt5.QtGui import QIcon, QPainter, QColor
from PyQt5.QtCore import QThread, Qt, QTimer


# ================= AUDIO THREAD =================
class AudioThread(QThread):
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.index = 0
        self.angle = 0.0

        self.visual_samples = np.zeros(256)

    def load(self, file):
        y, self.sr = librosa.load(file, mono=True)
        y = y / max(np.max(np.abs(y)), 1e-6)
        self.mono = y.astype(np.float32)
        self.index = 0
        self.angle = 0.0

    def callback(self, outdata, frames, time, status):
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)

        for i in range(frames):
            if self.index >= len(self.mono):
                self.index = 0

            base = float(self.mono[self.index]) * self.volume
            self.visual_samples[i % 256] = base

            pan = (math.sin(self.angle) + 1) * 0.5
            self.angle += 0.0006

            L, R = base, base

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

            self.index += 1

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


# ================= SPECTRUM =================
class Spectrum(QWidget):
    def __init__(self, audio):
        super().__init__()
        self.audio = audio
        self.setMinimumHeight(260)

    def paintEvent(self, e):
        if self.audio.visual_samples is None:
            return

        fft = np.abs(np.fft.rfft(self.audio.visual_samples))
        fft = fft[:64]

        painter = QPainter(self)
        w = self.width() / len(fft)

        for i, v in enumerate(fft):
            h = min(v * 40, self.height())
            color = QColor.fromHsv((i * 6) % 360, 255, 255)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(int(i*w), self.height()-h, int(w-2), int(h))


# ================= UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 DJ Music Player")
        self.resize(1000, 600)

        self.audio = AudioThread()
        self.files = []

        main = QWidget()
        self.setCentralWidget(main)
        root = QVBoxLayout(main)

        # ===== Progress Bar =====
        self.progress = QSlider(Qt.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderReleased.connect(self.seek)
        root.addWidget(self.progress)

        # ===== Center =====
        center = QHBoxLayout()
        root.addLayout(center)

        # ===== Playlist Table =====
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["", "Track", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 40)
        self.table.cellDoubleClicked.connect(self.play_selected)
        center.addWidget(self.table, 1)

        # ===== Spectrum =====
        self.spectrum = Spectrum(self.audio)
        center.addWidget(self.spectrum, 2)

        # ===== Controls =====
        controls = QHBoxLayout()
        root.addLayout(controls)

        def round_btn(icon):
            b = QPushButton()
            b.setIcon(QIcon(icon))
            b.setFixedSize(56, 56)
            b.setStyleSheet("border-radius:28px;background:#222;")
            return b

        self.btn_prev = round_btn("icons/prev.png")
        self.btn_play = round_btn("icons/play.png")
        self.btn_next = round_btn("icons/next.png")

        self.btn_prev.clicked.connect(self.prev)
        self.btn_next.clicked.connect(self.next)
        self.btn_play.clicked.connect(self.toggle)

        controls.addWidget(self.btn_prev)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_next)

        # ===== Volume =====
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.setFixedWidth(120)
        self.volume.valueChanged.connect(
            lambda v: setattr(self.audio, "volume", v/100)
        )

        controls.addWidget(QLabel("🔊"))
        controls.addWidget(self.volume)

        # ===== Effects =====
        self.effects = QComboBox()
        self.effects.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects.currentTextChanged.connect(
            lambda e: setattr(self.audio, "effect", e)
        )
        controls.addWidget(self.effects)

        # ===== Load =====
        load = QPushButton("📂 Load Folder")
        load.clicked.connect(self.load_folder)
        root.addWidget(load)

        # ===== Timers =====
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(30)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return

        self.files.clear()
        self.table.setRowCount(0)

        for f in os.listdir(folder):
            if f.lower().endswith((".mp3", ".wav")):
                r = self.table.rowCount()
                self.table.insertRow(r)

                d = QTableWidgetItem()
                d.setIcon(QIcon("icons/disk.png"))

                n = QTableWidgetItem(f)

                m = QTableWidgetItem()
                m.setIcon(QIcon("icons/music.png"))

                self.table.setItem(r, 0, d)
                self.table.setItem(r, 1, n)
                self.table.setItem(r, 2, m)

                self.files.append(os.path.join(folder, f))

    def play_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return

        self.audio.load(self.files[row])
        if not self.audio.isRunning():
            self.audio.start()

        self.audio.running = True
        self.btn_play.setIcon(QIcon("icons/pause.png"))

    def toggle(self):
        self.audio.running = not self.audio.running
        self.btn_play.setIcon(
            QIcon("icons/pause.png" if self.audio.running else "icons/play.png")
        )

    def seek(self):
        if self.audio.mono is None:
            return
        pos = self.progress.value() / 1000
        self.audio.index = int(len(self.audio.mono) * pos)

    def update_ui(self):
        if self.audio.mono is None:
            return
        self.progress.setValue(
            int((self.audio.index / len(self.audio.mono)) * 1000)
        )
        self.spectrum.update()

    def next(self):
        r = (self.table.currentRow() + 1) % len(self.files)
        self.table.selectRow(r)
        self.play_selected()

    def prev(self):
        r = (self.table.currentRow() - 1) % len(self.files)
        self.table.selectRow(r)
        self.play_selected()

    def closeEvent(self, e):
        self.audio.stop()
        e.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MusicPlayer()
    w.show()
    sys.exit(app.exec_())
