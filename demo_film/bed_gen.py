#!/usr/bin/env python3
"""Synthesize the film's original ambient music bed (no samples, no libraries
beyond numpy): slow A-minor drift, soft shimmer, low pulse, gentle noise wash.
Length follows durations.json; written to demo_film/bed.wav for merge.py."""
import json
import wave

import numpy as np

ROOT = "/home/k/Prototype/Amazon"
FILM = f"{ROOT}/demo_film"
SR = 48000


def tone(n, f, detune=0.0):
    t = np.arange(n) / SR
    a = np.sin(2 * np.pi * f * t)
    b = np.sin(2 * np.pi * (f * (1 + detune)) * t)
    return 0.5 * (a + b)


def env_segments(n, seg_s, fade_s):
    """Raised-cosine amplitude envelope with slow alternating segments."""
    env = np.ones(n, dtype=np.float64)
    step = int(seg_s * SR)
    fade = int(fade_s * SR)
    idx = np.arange(n)
    period = max(step, fade * 2)
    phase = (idx % period).astype(np.float64)
    env = 0.55 + 0.45 * np.sin(2 * np.pi * phase / period - np.pi / 2)
    return env


def main():
    scenes = json.load(open(f"{FILM}/durations.json"))["scenes"]
    total = sum(s["total_s"] for s in scenes)
    n = int((total + 2.0) * SR)
    t = np.arange(n) / SR

    # --- two slowly crossfading chords (A minor drift -> F -> C -> back) ------
    chords = [
        (110.00, 164.81, 220.00, 261.63, 329.63),   # A2 E3 A3 C4 E4
        (87.31, 130.81, 174.61, 220.00, 261.63),    # F2 C3 F3 A3 C4
        (98.00, 146.83, 196.00, 261.63, 329.63),    # G2 D3 G3 C4 E4
    ]
    seg = 17.0
    fade = 5.0
    period = seg * len(chords)
    idx = t
    phase = (idx % period) / period * len(chords)
    mix = np.zeros(n, dtype=np.float64)
    for c, tones in enumerate(chords):
        w = np.clip(np.cos(2 * np.pi * (phase - c)), 0.0, 1.0) ** 2
        for i, f in enumerate(tones):
            amp = 0.055 / (1 + i * 0.6)
            mix += amp * (w * tone(n, f, detune=0.0012)) * env_segments(n, seg, fade)

    # --- shimmer: high sparkle, slow tremolo ---------------------------------
    for f, amp in ((659.26, 0.012), (880.0, 0.008), (1318.5, 0.005)):
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.061 * t + f)
        mix += amp * lfo * np.sin(2 * np.pi * f * t)

    # --- soft heartbeat pulse every 8 s (sub energy, "a living home") --------
    pulse_n = int(1.4 * SR)
    pt = np.arange(pulse_n) / SR
    pulse = np.sin(2 * np.pi * 52.0 * pt) * np.exp(-pt * 3.2)
    for k in range(int(total // 8) + 1):
        s = int((k * 8.0 + 1.0) * SR)
        if s + pulse_n < n:
            mix[s:s + pulse_n] += 0.045 * pulse

    # --- air: gently low-passed noise wash (FFT rolloff, fast) ---------------
    rng = np.random.default_rng(7)
    noise = rng.standard_normal(n)
    freqs = np.fft.rfftfreq(n, d=1.0 / SR)
    spec = np.fft.rfft(noise)
    lp = np.fft.irfft(spec / (1.0 + (freqs / 380.0) ** 2), n=n)
    mix += 0.10 * lp

    # --- master: gentle saturation, fades, level -----------------------------
    mix = np.tanh(mix * 1.1)
    fi = int(2.0 * SR)
    fo = int(3.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi) ** 2
    mix[-fo:] *= np.linspace(1, 0, fo) ** 2
    peak = np.max(np.abs(mix)) or 1.0
    mix = mix / peak * 0.30                     # ~ -10.5 dBFS peak
    stereo = np.stack([mix, np.roll(mix, int(0.013 * SR))], axis=1)

    pcm = (stereo * 32767.0).astype(np.int16)
    out = f"{FILM}/bed.wav"
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    rms = float(np.sqrt(np.mean(stereo ** 2)))
    print(f"bed: {out}  {total + 2.0:.1f}s  rms={20 * np.log10(rms + 1e-9):.1f} dBFS")


if __name__ == "__main__":
    main()
