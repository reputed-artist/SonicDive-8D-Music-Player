import math
import numpy as np

class Effect8D:
    def __init__(self, samplerate,
                 rotation_speed=0.8,
                 reverb_amount=0.2,
                 depth_strength=0.3):

        self.sr = samplerate
        self.rotation_speed = rotation_speed
        self.reverb_amount = reverb_amount
        self.depth_strength = depth_strength

        self.angle = 0
        self.index = 0

    def process(self, mono, frames):
        left = np.zeros(frames, dtype=np.float32)
        right = np.zeros(frames, dtype=np.float32)

        for i in range(frames):
            if self.index >= len(mono):
                self.index = 0

            self.angle += self.rotation_speed / self.sr
            pan = (math.sin(self.angle) + 1) / 2
            depth = 1 - (math.cos(self.angle) * self.depth_strength)

            l = mono[self.index] * (1 - pan) * depth
            r = mono[self.index] * pan * depth

            if self.index > 500:
                l += mono[self.index - 500] * self.reverb_amount
                r += mono[self.index - 500] * self.reverb_amount

            left[i] = l
            right[i] = r

            self.index += 1

        return np.column_stack((left, right))
