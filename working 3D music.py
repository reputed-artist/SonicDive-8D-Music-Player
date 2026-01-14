import sounddevice as sd
import numpy as np
import soundfile as sf
import math

# 8D Settings
rotation_speed = 0.7
reverb_amount = 0.12
angle = 0

# Load audio file
filename = "song.wav"   # CHANGE TO YOUR FILE
audio, samplerate = sf.read(filename)

# Ensure stereo
if len(audio.shape) == 1:
    audio = np.column_stack((audio, audio))

# Normalize
audio = audio.astype(np.float32)

position = 0

def callback(outdata, frames, time, status):
    global position, angle

    if status:
        print(status)

    # Handle end of file
    end = position + frames
    if end >= len(audio):
        outdata[:] = np.zeros((frames, 2), dtype='float32')
        raise sd.CallbackStop()

    chunk = audio[position:end]
    position = end

    # Convert to mono for effect
    mono = chunk.mean(axis=1)

    # Pan rotation
    angle += rotation_speed * (frames / samplerate)
    pan = (math.sin(angle) + 1) / 2

    left = mono * (1 - pan)
    right = mono * pan
    stereo = np.column_stack((left, right))

    # Reverb effect
    echo = np.roll(stereo, 1500, axis=0) * reverb_amount
    stereo += echo

    outdata[:] = stereo.astype(np.float32)

print("🎧 Playing 8D Audio from File...")

with sd.OutputStream(
    channels=2,
    samplerate=samplerate,
    callback=callback,
    dtype='float32'
):
    sd.sleep(int((len(audio) / samplerate) * 1000))
