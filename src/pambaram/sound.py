import math
import random
from array import array

import pygame


class SoundManager:
    """Procedurally synthesizes short SFX at runtime (no audio assets needed,
    no extra dependency) and caches them as pygame.mixer.Sound objects."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self._cache = {}
        self._channels = 2
        self._rate = 44100

        if self.enabled:
            try:
                info = pygame.mixer.get_init()
                if not info:
                    self.enabled = False
                    return
                rate, size, channels = info
                if abs(size) != 16:
                    # Only 16-bit PCM synthesis is implemented; anything else,
                    # skip sound rather than emit garbled audio.
                    self.enabled = False
                    return
                self._rate = rate
                self._channels = max(1, channels)
                self._build_all()
            except Exception:
                self.enabled = False

    def _tone(self, freq, duration, volume=0.5, wave="sine", decay=6.0, freq_end=None):
        n = max(1, int(self._rate * duration))
        buf = array("h")
        for i in range(n):
            t = i / self._rate
            progress = i / max(1, n - 1)
            f = freq if freq_end is None else freq + (freq_end - freq) * progress
            if wave == "square":
                s = 1.0 if math.sin(2 * math.pi * f * t) >= 0 else -1.0
            elif wave == "noise":
                s = random.uniform(-1, 1)
            else:
                s = math.sin(2 * math.pi * f * t)
            env = math.exp(-decay * progress)
            sample = int(max(-1.0, min(1.0, s * env * volume)) * 32767)
            for _ in range(self._channels):
                buf.append(sample)
        return buf

    def _make(self, name, segments):
        buf = array("h")
        for seg in segments:
            buf.extend(seg)
        try:
            self._cache[name] = pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            pass

    def _build_all(self):
        self._make("click", [self._tone(720, 0.05, 0.35, "square", decay=10)])
        self._make("launch", [self._tone(180, 0.22, 0.5, "sine", decay=4.0, freq_end=420)])
        self._make("dash", [self._tone(300, 0.12, 0.4, "square", decay=8.0, freq_end=520)])
        self._make("collision", [self._tone(90, 0.12, 0.55, "noise", decay=9.0)])
        self._make("special", [
            self._tone(440, 0.08, 0.45, "sine", decay=3.0, freq_end=660),
            self._tone(660, 0.14, 0.45, "sine", decay=4.0, freq_end=880),
        ])
        self._make("ringout", [self._tone(500, 0.35, 0.5, "sine", decay=2.5, freq_end=90)])
        self._make("victory", [
            self._tone(523, 0.12, 0.4, "sine", decay=3.0),
            self._tone(659, 0.12, 0.4, "sine", decay=3.0),
            self._tone(784, 0.25, 0.45, "sine", decay=2.5),
        ])

    def play(self, name):
        if not self.enabled:
            return
        snd = self._cache.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass
