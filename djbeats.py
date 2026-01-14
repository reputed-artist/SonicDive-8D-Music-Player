import librosa
import numpy as np
import sounddevice as sd
import scipy.signal as sig

input_file = "output_8d.wav"

dj_intensity = 0.8
bass_boost = 6
block_size = 1024

# Load STEREO
y, sr = librosa.load(input_file, mono=False)

# If mono file → make stereo
if y.ndim == 1:
    y = np.vstack([y, y])

left, right = y
length = left.shape[0]

# Beat detection (mono for analysis only)
mono = librosa.to_mono(y)
tempo, beats = librosa.beat.beat_track(y=mono, sr=sr)
beat_samples = (librosa.frames_to_time(beats, sr=sr) * sr).astype(int)

print(f"🎧 {int(tempo)} BPM | DJ MODE")

# ---------- Filters ----------
def butter_band(low, high):
    return sig.butter(2, [low/(sr/2), high/(sr/2)], btype='band')

def butter_low(cut):
    return sig.butter(2, cut/(sr/2), btype='low')

def butter_high(cut):
    return sig.butter(2, cut/(sr/2), btype='high')

b_bass, a_bass = butter_low(150)
b_mid, a_mid   = butter_band(150, 4000)
b_high, a_high = butter_high(4000)

# Filter states
zb_l = sig.lfilter_zi(b_bass, a_bass)
zm_l = sig.lfilter_zi(b_mid, a_mid)
zh_l = sig.lfilter_zi(b_high, a_high)

zb_r = sig.lfilter_zi(b_bass, a_bass)
zm_r = sig.lfilter_zi(b_mid, a_mid)
zh_r = sig.lfilter_zi(b_high, a_high)

idx = 0

def callback(outdata, frames, time, status):
    global idx
    chunk_l = np.zeros(frames)
    chunk_r = np.zeros(frames)

    for i in range(frames):
        if idx >= length:
            idx = 0

        l = left[idx]
        r = right[idx]

        # Split bands
        bass_l, zb_l[:] = sig.lfilter(b_bass, a_bass, [l], zi=zb_l)
        mid_l,  zm_l[:] = sig.lfilter(b_mid, a_mid, [l], zi=zm_l)
        high_l, zh_l[:] = sig.lfilter(b_high, a_high, [l], zi=zh_l)

        bass_r, zb_r[:] = sig.lfilter(b_bass, a_bass, [r], zi=zb_r)
        mid_r,  zm_r[:] = sig.lfilter(b_mid, a_mid, [r], zi=zm_r)
        high_r, zh_r[:] = sig.lfilter(b_high, a_high, [r], zi=zh_r)

        gain = 1.0
        if idx in beat_samples:
            gain += dj_intensity

        # Boost bass only
        out_l = bass_l[0] * (1 + bass_boost/10) * gain + mid_l[0] + high_l[0]
        out_r = bass_r[0] * (1 + bass_boost/10) * gain + mid_r[0] + high_r[0]

        chunk_l[i] = out_l
        chunk_r[i] = out_r

        idx += 1

    outdata[:] = np.column_stack((chunk_l, chunk_r))


with sd.OutputStream(
    samplerate=sr,
    channels=2,
    dtype="float32",
    blocksize=block_size,
    callback=callback
):
    sd.sleep(999999999)
