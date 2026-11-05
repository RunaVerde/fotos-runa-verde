import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 44100; DUR = 24.5; N = int(SR * DUR)
rng = np.random.default_rng(21)
L = np.zeros(N); R = np.zeros(N)
BPM = 84; BEAT = 60 / BPM

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt((1 - pan) / 2); R[i:j] += s * np.sqrt((1 + pan) / 2)

# Escala frígia dominante em D (som "oriental/místico"): D Eb F# G A Bb C
SCALE = [62, 63, 66, 67, 69, 70, 72, 74, 75, 78, 79, 81]

# 1) Coro / pad com formantes (vogal "aah")
def choir(notes, length, gain):
    n = int(length * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        f = hz(m)
        for det in (-0.35, 0.0, 0.4):
            ph = rng.uniform(0, 6.28)
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + ph)
            saw = np.zeros(n)
            for h in range(1, 14):
                saw += np.sin(2 * np.pi * f * (1 + det / 100) * h * np.cumsum(vib) / SR + ph * h) / h
            s += saw
    # formantes de "a" (~700 Hz e ~1200 Hz)
    out = np.zeros(n)
    for lo, hi, g in ((550, 900, 1.0), (1000, 1400, 0.6), (2300, 2900, 0.25)):
        out += sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), s) * g
    env = np.minimum(1, t / 2.0) * np.minimum(1, (length - t) / 2.0)
    return out * env * gain / len(notes)

add(choir([50, 57, 62, 66], 9.0, 0.22), 0.0)
add(choir([46, 53, 58, 62], 6.0, 0.22), 8.0)
add(choir([48, 55, 60, 67], 5.5, 0.22), 13.0)
add(choir([50, 57, 62, 66, 69], 7.0, 0.26), 17.8)

# 2) Drone grave
n = N; t = np.arange(n) / SR
drone = (np.sin(2 * np.pi * hz(38) * t) + 0.5 * np.sin(2 * np.pi * hz(45) * t) + 0.3 * np.sin(2 * np.pi * hz(50) * t * 1.001))
drone *= (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t)) * np.minimum(1, t / 3) * np.minimum(1, (DUR - t) / 2.5)
add(drone, 0, gain=0.10)

# 3) Handpan (notas metálicas suaves) em padrão rítmico a partir de 3 s
def handpan(f, length=2.6):
    n = int(length * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 2.5)
         + 0.25 * np.sin(2 * np.pi * f * 2.98 * t) * np.exp(-t * 4) + 0.15 * np.sin(2 * np.pi * f * 0.5 * t))
    att = np.minimum(1, t / 0.006)
    return s * att * np.exp(-t * 1.6)
pattern = [0, 4, 7, 4, 2, 4, 9, 7, 0, 5, 7, 4, 2, 1, 0, 4]
step = BEAT / 2
tcur = 3.0; k = 0
while tcur < 22.8:
    if not (10.0 < tcur < 10.4):
        m = SCALE[pattern[k % len(pattern)]]
        if k % 8 == 0: m -= 12
        acc = 1.0 if k % 4 == 0 else 0.65
        add(handpan(hz(m)), tcur + rng.normal(0, 0.006), pan=0.35 * np.sin(k * 0.9), gain=0.16 * acc)
    tcur += step; k += 1

# 4) Tambor xamânico (frame drum) + shaker
def drum(gain=1.0):
    n = int(0.9 * SR); t = np.arange(n) / SR
    f = 75 * np.exp(-t * 10) + 52
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    skin = sosfilt(butter(2, [180, 900], btype="band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 30) * 0.4
    return (body + skin) * gain
def shaker():
    n = int(0.12 * SR); t = np.arange(n) / SR
    return sosfilt(butter(2, 5000, btype="high", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-t * 40)
b = 0; tcur = 3.0
while tcur < 23.0:
    pos = b % 8
    if pos in (0, 3, 4): add(drum(0.55 if pos == 0 else 0.35), tcur)
    if tcur > 6.5: add(shaker(), tcur + BEAT / 2, pan=0.4, gain=0.05)
    tcur += BEAT / 2 * 2 if pos in (7,) else BEAT / 2; b += 1

# 5) Tigela tibetana nos momentos de revelação
def bowl(f, length=6.0):
    n = int(length * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) * (1 + 0.3 * np.sin(2 * np.pi * 4.5 * t))
         + 0.5 * np.sin(2 * np.pi * f * 2.71 * t) * np.exp(-t * 0.8) + 0.3 * np.sin(2 * np.pi * f * 5.1 * t) * np.exp(-t * 1.5))
    return s * np.minimum(1, t / 0.02) * np.exp(-t * 0.55)
for st, f in ((0.15, hz(62)), (3.0, hz(57)), (10.0, hz(62)), (18.9, hz(50))):
    add(bowl(f), st, gain=0.16)

# 6) Harpa (glissando) nas transições
def harp_note(f):
    n = int(1.8 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t * 2.2) * np.minimum(1, t / 0.003)
for st in (2.3, 9.4, 18.3):
    for i, m in enumerate(SCALE + [x + 12 for x in SCALE[:5]]):
        add(harp_note(hz(m)), st + i * 0.045, pan=-0.6 + i * 0.07, gain=0.07)

# 7) Risers + impacto grave
def riser(length):
    n = int(length * SR); s = sosfilt(butter(2, [700, 7000], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    return s * np.linspace(0, 1, n) ** 2.5 * 0.16
def boom():
    n = int(2.4 * SR); t = np.arange(n) / SR; f = 60 * np.exp(-t * 3) + 36
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
for st in (3.0, 10.0, 19.0):
    add(riser(1.8), st - 1.8); add(boom(), st, gain=0.75)

# Reverb e master
def reverb(x, secs=3.4, mix=0.42):
    n = int(secs * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (1.0 * SR)); ir /= np.sqrt((ir ** 2).sum())
    return x * (1 - mix) + fftconvolve(x, ir)[: len(x)] * mix * 1.7
mix = np.stack([reverb(L), reverb(R)], 1)
fade = np.ones(N); fi = int(0.3 * SR); fo = int(2.4 * SR)
fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
mix *= fade[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.6) / np.tanh(1.6) * 0.92
wavfile.write("/home/claude/mistica/trilha-caixa.wav", SR, (mix * 32767).astype(np.int16))
print("ok")
