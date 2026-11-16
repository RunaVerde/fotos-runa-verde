"""Trilha celta original (ré dórico): bordão de gaita, harpa dedilhada, flauta irlandesa e bodhrán. 24 s."""
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile

SR = 44100; DUR = 24.0; N = int(SR * DUR)
rng = np.random.default_rng(61)
L = np.zeros(N); R = np.zeros(N)
BPM = 96; B = 60 / BPM; E = B / 3  # compasso 6/8: colcheia = E
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def add(sig, st, pan=0.0, g=1.0):
    i = max(0, int(st * SR)); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[:j - i] * g; L[i:j] += s * np.sqrt((1 - pan) / 2); R[i:j] += s * np.sqrt((1 + pan) / 2)

def harp(f, dur=2.5):
    n = int(SR * dur); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return out * np.exp(-np.arange(n) / SR * 1.2)

def whistle(f, dur):
    n = int(SR * dur); t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    s = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    br = sosfilt(butter(2, [f * 0.9, f * 3], btype='band', fs=SR, output='sos'), rng.standard_normal(n)) * 0.06
    env = np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.06).clip(0)
    return (s + br) * env

def bodhran(accent=1.0):
    n = int(SR * 0.45); t = np.arange(n) / SR
    f = 70 + 60 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    hit = sosfilt(butter(2, 900, btype='low', fs=SR, output='sos'), rng.standard_normal(n)) * np.exp(-t * 60) * 0.5
    return (s + hit) * accent

# bordão (ré + lá) durante tudo
t = np.arange(N) / SR
dr = np.zeros(N)
for m, g in ((38, 0.5), (45, 0.35), (50, 0.2)):
    ph = 2 * np.pi * hz(m) * t + 0.3 * np.sin(2 * np.pi * 0.2 * t)
    dr += g * (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph))
dr = sosfilt(butter(2, 900, btype='low', fs=SR, output='sos'), dr)
dr *= np.clip(t / 2.5, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1) * 0.14
L += dr; R += dr

# harpa: arpejos por compasso (Dm, C, Dm, Am / F, C, G, Dm)
chords = [[50, 57, 62, 65, 69], [48, 55, 60, 64, 67], [50, 57, 62, 65, 69], [45, 52, 57, 60, 64],
          [41, 48, 53, 57, 60], [48, 55, 60, 64, 67], [43, 50, 55, 59, 62], [50, 57, 62, 65, 69]]
bar = 6 * E; nb = int(DUR / bar) + 1
for k in range(nb):
    ch = chords[k % 8]; st = k * bar
    for i, idx in enumerate([0, 2, 3, 4, 3, 2]):
        add(harp(hz(ch[idx]), 2.0), st + i * E + rng.normal(0, 0.004), pan=-0.35 + 0.12 * i, g=0.32)

# melodia (flauta) – entra no 3 s e vai até ~19 s; frase original em ré dórico
D4, E4, F4, G4, A4, B4, C5, D5, E5 = 62, 64, 65, 67, 69, 71, 72, 74, 76
mel = [(D4, 3), (A4, 3), (G4, 2), (F4, 1), (E4, 3),
       (D4, 2), (F4, 1), (A4, 3), (C5, 2), (A4, 1), (D5, 3),
       (C5, 2), (A4, 1), (G4, 3), (F4, 2), (E4, 1), (D4, 3),
       (A4, 3), (D5, 3), (C5, 2), (A4, 1), (G4, 3), (D4, 6)]
st = 3 * bar if 3 * bar < 3.6 else 3.0
st = round(3.0 / bar) * bar
tt = st
for m, d in mel:
    if tt > 20.5: break
    add(whistle(hz(m + 12), d * E * 0.95), tt, pan=0.15, g=0.20)
    tt += d * E

# bodhrán a partir do gancho (3 s) até 19 s, mais forte nas batidas
k = 0; tt = st
while tt < 19.5:
    acc = 1.0 if k % 6 == 0 else (0.6 if k % 3 == 0 else 0.3)
    add(bodhran(acc), tt + rng.normal(0, 0.003), pan=-0.1, g=0.35)
    tt += E; k += 1
# golpes nos 3 momentos de "impacto"
for h in (3.0, 10.0, 19.0):
    add(bodhran(1.4), h, g=0.5)
    for i, m in enumerate([74, 77, 81, 86]): add(harp(hz(m), 2.5), h + i * 0.05, pan=-0.3 + 0.2 * i, g=0.22)

def reverb(x, secs=2.6, mix=0.32):
    n = int(secs * SR); ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (0.7 * SR)); ir /= np.sqrt((ir ** 2).sum())
    return x * (1 - mix) + fftconvolve(x, ir)[:len(x)] * mix * 1.6
mix = np.stack([reverb(L), reverb(R)], 1)
fade = np.ones(N); fo = int(2.0 * SR); fade[-fo:] = np.linspace(1, 0, fo); mix *= fade[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.3) / np.tanh(1.3) * 0.9
wavfile.write('/home/claude/odin/trilha-odin.wav', SR, (mix * 32767).astype(np.int16))
print('ok')
