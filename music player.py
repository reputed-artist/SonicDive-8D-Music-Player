import sys, os, math
import numpy as np
import sounddevice as sd
import librosa

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QFileDialog, QLabel, QComboBox
)
from PyQt5.QtCore import QThread


# ================= AUDIO THREAD =================
class AudioThread(QThread):
    def __init__(self):
        super().__init__()

        self.running = False
        self.effect = "Normal"

        self.mono = None
        self.sr = 44100
        self.index = 0
        self.angle = 0.0

        # Effect tuning (SAFE VALUES)
        self.rotation_speed = 0.8
        self.depth_strength = 0.30
        self.reverb_amount = 0.20

    def load(self, file):
        y, self.sr = librosa.load(file, mono=True)
        y = y / max(np.max(np.abs(y)), 1e-6)
        self.mono = y.astype(np.float32)

        self.index = 0
        self.angle = 0.0

    def set_effect(self, effect):
        self.effect = effect


    # def callback(self, outdata, frames, time, status):
    #     if not self.running or self.mono is None:
    #         outdata[:] = np.zeros((frames, 2), dtype=np.float32)
    #         return

    #     out = np.zeros((frames, 2), dtype=np.float32)

    #     for i in range(frames):
    #         if self.index >= len(self.mono):
    #             self.index = 0

    #         base = float(self.mono[self.index])

    #         # Time-based movement (stable)
    #         self.angle += self.rotation_speed * (1.0 / self.sr)

    #         pan = (math.sin(self.angle) + 1) * 0.5
    #         depth = 1.0 - (math.cos(self.angle) * self.depth_strength)

    #         out_l = base
    #         out_r = base

    #         # ================= EFFECTS =================
    #         if self.effect == "8D":
    #             spatial_gain = 1.35  # loudness compensation

    #             out_l = base * (1 - pan) * depth * spatial_gain
    #             out_r = base * pan * depth * spatial_gain

    #             # subtle echo (space)
    #             delay = 600
    #             if self.index > delay:
    #                 echo = self.mono[self.index - delay] * 0.18
    #                 out_l += echo
    #                 out_r += echo

    #         elif self.effect == "3D":
    #             spatial_gain = 1.25

    #             out_l = base * (1 - pan) * spatial_gain
    #             out_r = base * pan * spatial_gain

    #         elif self.effect == "Dolby":
    #             # True stereo widening (mid/side)
    #             mid = base
    #             side = math.sin(self.angle) * 0.25

    #             bass = base * 0.22
    #             presence = mid * 0.15

    #             out_l = mid + side + bass + presence
    #             out_r = mid - side + bass + presence

    #         elif self.effect == "Rock":
    #             out_l = base * 1.35
    #             out_r = base * 1.35

    #         elif self.effect == "Jazz":
    #             out_l = base * 0.95
    #             out_r = base * 0.95

    #         # 🛡 Soft limiter (important)
    #         out[i, 0] = np.tanh(out_l)
    #         out[i, 1] = np.tanh(out_r)

    #         self.index += 1

    #     outdata[:] = out

    def callback(self, outdata, frames, time, status):
        if not self.running or self.mono is None:
            outdata[:] = np.zeros((frames, 2), dtype=np.float32)
            return

        out = np.zeros((frames, 2), dtype=np.float32)

        for i in range(frames):
            if self.index >= len(self.mono):
                self.index = 0

            base = float(self.mono[self.index])

            # Time-based motion
            self.angle += self.rotation_speed * (1.0 / self.sr)
            pan = (math.sin(self.angle) + 1) * 0.5
            depth = 1.0 - (math.cos(self.angle) * self.depth_strength)

            # Default
            out_l = base
            out_r = base

            # ===================== GENRE EFFECTS =====================

            if self.effect == "Flat":
                out_l = base
                out_r = base

            elif self.effect == "Pop":
                bass = base * 0.25
                presence = base * 0.35
                out_l = base + bass + presence
                out_r = base + bass + presence

            elif self.effect == "Classical":
                out_l = base * 1.1
                out_r = base * 1.1

            elif self.effect == "Hip Hop":
                sub = base * 0.45
                punch = base * 0.25
                out_l = base + sub + punch
                out_r = base + sub + punch

            elif self.effect == "Folk":
                warmth = base * 0.2
                out_l = base + warmth
                out_r = base + warmth

            elif self.effect == "Dance":
                bass = base * 0.4
                sparkle = math.sin(self.angle * 3) * 0.15
                out_l = base + bass + sparkle
                out_r = base + bass + sparkle

            elif self.effect == "Rock":
                out_l = base * 1.35
                out_r = base * 1.35

            elif self.effect == "3D":
                gain = 1.3
                out_l = base * (1 - pan) * gain
                out_r = base * pan * gain

            elif self.effect == "8D":
                gain = 1.4
                out_l = base * (1 - pan) * depth * gain
                out_r = base * pan * depth * gain

                delay = 600
                if self.index > delay:
                    echo = self.mono[self.index - delay] * 0.18
                    out_l += echo
                    out_r += echo

            elif self.effect == "Dolby":
                mid = base * 1.1
                side = math.sin(self.angle) * 0.25
                bass = base * 0.3
                out_l = mid + side + bass
                out_r = mid - side + bass

            # Soft limiter
            out[i, 0] = np.tanh(out_l)
            out[i, 1] = np.tanh(out_r)

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
                sd.sleep(50)

    def stop(self):
        self.running = False


# ================= UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("🎧 PyQt5 DJ Music Player")
        self.setGeometry(200, 100, 900, 600)

        self.audio = AudioThread()
        self.files = []
        self.current_index = 0

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Playlist
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.play_selected)
        layout.addWidget(self.list)

        # Controls
        controls = QHBoxLayout()

        self.btn_prev = QPushButton("⏮")
        self.btn_play = QPushButton("▶")
        self.btn_pause = QPushButton("⏸")
        self.btn_next = QPushButton("⏭")

        self.btn_prev.clicked.connect(self.prev_track)
        self.btn_play.clicked.connect(self.play_selected)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_next.clicked.connect(self.next_track)

        controls.addWidget(self.btn_prev)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_pause)
        controls.addWidget(self.btn_next)

        # Effects
        self.effects = QComboBox()
        #self.effects.addItems(["Normal", "3D", "8D", "Rock", "Jazz", "Dolby"])
        self.effects.addItems([
    "Flat",
    "Pop",
    "Classical",
    "Hip Hop",
    "Folk",
    "Dance",
    "Rock",
    "3D",
    "8D",
    "Dolby"
])

        self.effects.currentTextChanged.connect(self.audio.set_effect)

        controls.addWidget(QLabel("Effect:"))
        controls.addWidget(self.effects)

        layout.addLayout(controls)

        # Folder button
        self.btn_folder = QPushButton("📂 Add Folder")
        self.btn_folder.clicked.connect(self.load_folder)
        layout.addWidget(self.btn_folder)

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return

        self.files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith((".mp3", ".wav"))
        ]

        self.list.clear()
        for f in self.files:
            self.list.addItem(os.path.basename(f))

    def play_selected(self):
        if not self.files:
            return

        self.current_index = max(0, self.list.currentRow())
        self.audio.load(self.files[self.current_index])

        if not self.audio.isRunning():
            self.audio.start()
        else:
            self.audio.running = True

    def pause(self):
        self.audio.running = False

    def next_track(self):
        if not self.files:
            return
        self.current_index = (self.current_index + 1) % len(self.files)
        self.list.setCurrentRow(self.current_index)
        self.play_selected()

    def prev_track(self):
        if not self.files:
            return
        self.current_index = (self.current_index - 1) % len(self.files)
        self.list.setCurrentRow(self.current_index)
        self.play_selected()

    def closeEvent(self, event):
        self.audio.stop()
        event.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
