import numpy as np
import soundfile as sf
import sounddevice as sd
from pydub import AudioSegment
import math

# -----------------------------
# USER SETTINGS
# -----------------------------
rotation_speed = 0.8     # 0.3 slow – 1.5 fast
reverb_amount = 0.20     # 0.0 – 0.3
depth_strength = 0.30    # 0.1 – 0.5
input_file = "song.wav"  # WAV needed
# -----------------------------

print("🎧 Loading audio...")
audio = AudioSegment.from_wav(input_file)
samples = np.array(audio.get_array_of_samples()).astype(np.float32)
samples /= np.max(np.abs(samples))  # normalize

samplerate = audio.frame_rate

# Convert to mono
if audio.channels == 2:
    samples = samples.reshape((-1, 2))
    mono = samples.mean(axis=1)
else:
    mono = samples

print("🎵 Starting LIVE 8D playback...\nPress CTRL+C to stop\n")

angle = 0
index = 0

def audio_callback(outdata, frames, time, status):
    global angle, index

    if status:
        print(status)

    chunk_left = []
    chunk_right = []

    for _ in range(frames):
        if index >= len(mono):
            index = 0   # loop song

        angle += rotation_speed * (1.0 / samplerate)
        pan = (math.sin(angle) + 1) / 2
        depth = 1 - (math.cos(angle) * depth_strength)

        left = mono[index] * (1 - pan) * depth
        right = mono[index] * pan * depth

        # reverb (simple echo)
        if index > 500:
            left += mono[index-500] * reverb_amount
            right += mono[index-500] * reverb_amount

        chunk_left.append(left)
        chunk_right.append(right)

        index += 1

    stereo_chunk = np.column_stack((chunk_left, chunk_right)).astype(np.float32)
    outdata[:] = stereo_chunk

# Start stream
with sd.OutputStream(channels=2, callback=audio_callback, samplerate=samplerate):
    sd.sleep(int(10000000))  # run "forever"
