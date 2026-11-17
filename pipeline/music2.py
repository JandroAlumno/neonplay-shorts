import numpy as np, wave
from scipy import signal
from timing import *

rng = np.random.default_rng(7)
n = int(SR * TOTAL) + SR * 2
L = np.zeros(n); R = np.zeros(n)
t_all = np.arange(n) / SR
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
def S(beat): return int(beat * BEAT * SR)
def lp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2): return signal.sosfilt(signal.butter(order, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return signal.sosfilt(signal.butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
def saw(f, x): return 2 * ((f * x) % 1) - 1
def add(buf, s, x, g=1.0):
    e = min(s + len(x), n)
    if e > s: buf[s:e] += g * x[:e - s]
def addst(s, x, gl=1.0, gr=None):
    add(L, s, x, gl); add(R, s, x, gl if gr is None else gr)

DRUM_END = BEATS_PER_SCENE * N_SCENES  # drums stop at outro
drums = np.zeros(n); snare_bus = np.zeros(n); music = np.zeros((2, n)); fx = np.zeros((2, n))

# ---- drums
for b in range(DRUM_END):
    s = S(b); x = np.arange(int(0.35 * SR)) / SR
    f = 45 + 130 * np.exp(-x * 35)
    kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 7)
    kick += 0.3 * rng.standard_normal(len(x)) * np.exp(-x * 300)  # click
    add(drums, s, np.tanh(1.6 * kick), 0.95)
    if b % 4 in (1, 3):
        xs = np.arange(int(0.3 * SR)) / SR
        sn = bp(rng.standard_normal(len(xs)), 600, 4500) * np.exp(-xs * 16) + 0.5 * np.sin(2 * np.pi * 190 * xs) * np.exp(-xs * 25)
        add(snare_bus, s, sn, 0.55)
    for q in range(4):  # 16th hats
        hs = S(b + q / 4); xh = np.arange(int((0.12 if q == 2 else 0.04) * SR)) / SR
        hat = lp(hp(rng.standard_normal(len(xh)), 7000), 12000) * np.exp(-xh * (25 if q == 2 else 90))
        add(drums, hs, hat, 0.1 if q == 2 else 0.05 + 0.02 * (q % 2))
# fill before scene 4 and scene 7
for sc in (4, 7):
    for k in range(8):
        s = S(sc * BEATS_PER_SCENE - 2 + k / 4); xs = np.arange(int(0.12 * SR)) / SR
        sn = bp(rng.standard_normal(len(xs)), 600, 4500) * np.exp(-xs * 30)
        add(snare_bus, s, sn, 0.2 + 0.05 * k)

# sidechain envelope
ph = (t_all % BEAT) / BEAT
sc_env = 1 - 0.75 * np.exp(-ph * 9)
sc_env[S(DRUM_END):] = 1

# ---- harmony: Am F C G per bar
chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
nbars = TOTAL_BEATS // 4 + 1
for k in range(nbars):
    s = S(k * 4); dur = 4 * BEAT; x = np.arange(int(dur * SR)) / SR
    ch = chords[k % 4]
    padL = sum(saw(mf(m + 12) * 0.997, x) + saw(mf(m) * 1.004, x) for m in ch)
    padR = sum(saw(mf(m + 12) * 1.003, x) + saw(mf(m) * 0.996, x) for m in ch)
    env = np.clip(x / 0.05, 0, 1) * np.clip((dur - x) / 0.05, 0, 1)
    music[0, s:s + len(x)][:max(0, min(len(x), n - s))] += (0.12 * lp(padL, 2200) * env)[:max(0, min(len(x), n - s))]
    music[1, s:s + len(x)][:max(0, min(len(x), n - s))] += (0.12 * lp(padR, 2200) * env)[:max(0, min(len(x), n - s))]
    # bass 8ths octave bounce
    if k * 4 < DRUM_END:
        for e in range(8):
            bs = S(k * 4 + e / 2); xb = np.arange(int(BEAT / 2 * SR * 0.85)) / SR
            note = ch[0] - 24 + (12 if e % 2 else 0)
            bb = lp(saw(mf(note), xb) + 0.5 * saw(mf(note) * 1.01, xb), 700 + 500 * np.exp(-0)) * np.exp(-xb * 5)
            add(music[0], bs, bb, 0.32); add(music[1], bs, bb, 0.32)
    # arp lead from bar 2 to end of drums
    if 2 <= k and k * 4 < DRUM_END:
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for e in range(16):
            a_s = S(k * 4 + e / 4); xa = np.arange(int(BEAT / 4 * SR)) / SR
            m = ch[pattern[e % 8]] + 12 + (12 if e >= 8 and e % 4 == 0 else 0)
            tone = lp(np.sign(np.sin(2 * np.pi * mf(m) * xa)) * 0.6 + saw(mf(m) * 1.006, xa) * 0.4, 3200) * np.exp(-xa * 10)
            pan = 0.35 if e % 2 else 0.65
            add(fx[0], a_s, tone, 0.17 * (1 - pan) * 2); add(fx[1], a_s, tone, 0.17 * pan * 2)

music *= sc_env
# delay on arp (dotted 8th)
d = S(0.75)
arp = fx.copy()
for i in range(1, 4):
    fx[0, d * i:] += arp[1, :-d * i] * (0.4 ** i); fx[1, d * i:] += arp[0, :-d * i] * (0.4 ** i)
fx *= (0.6 + 0.4 * sc_env)

# ---- transitions: whoosh + impact
sfx = np.zeros((2, n))
for sc in range(N_SCENES + 1):
    st = sc * BEATS_PER_SCENE
    big = sc in BIG or sc == N_SCENES
    if sc > 0:  # whoosh rising into the cut
        wl = (2.0 if big else 0.6) * BEAT * (2 if big else 1)
        xw = np.arange(int(wl * SR)) / SR
        noise = rng.standard_normal(len(xw))
        fc = np.geomspace(300, 9000, len(xw))
        y = np.zeros_like(noise); ylp = 0.0
        a = np.exp(-2 * np.pi * fc / SR)
        for i in range(len(noise)): ylp = a[i] * ylp + (1 - a[i]) * noise[i]; y[i] = ylp
        y = lp(y, 6000) * (xw / wl) ** 2 * 3
        s0 = S(st) - len(xw)
        add(sfx[0], s0, y, 0.35 if big else 0.18); add(sfx[1], s0, y[::-1][::-1] * 0.9, 0.35 if big else 0.18)
    xi = np.arange(int(1.4 * SR)) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-xi * 12)) / SR) * np.exp(-xi * (2.5 if big else 6))
    crash = hp(rng.standard_normal(len(xi)), 3000) * np.exp(-xi * (3 if big else 9))
    g = 0.7 if big else 0.35
    add(sfx[0], S(st), boom * g + crash * g * 0.18); add(sfx[1], S(st), boom * g + crash * g * 0.15)

# ---- reverb
def ir(seed, sec=1.6):
    r = np.random.default_rng(seed); x = np.arange(int(sec * SR)) / SR
    return r.standard_normal(len(x)) * np.exp(-x * 4) * 0.02
irL, irR = ir(1), ir(2)
rev_in = snare_bus + 0.4 * (music[0] + music[1]) / 2 + 0.6 * (fx[0] + fx[1]) / 2 + 0.3 * (sfx[0] + sfx[1]) / 2
revL = lp(signal.fftconvolve(rev_in, irL)[:n], 4500); revR = lp(signal.fftconvolve(rev_in, irR)[:n], 4500)

L = drums + snare_bus + music[0] + fx[0] + sfx[0] + 0.5 * revL
R = drums + snare_bus + music[1] + fx[1] + sfx[1] + 0.5 * revR
mix = np.stack([L, R])
mix = mix[:, :int(TOTAL * SR)]
tt = np.arange(mix.shape[1]) / SR
mix *= np.clip((mix.shape[1] / SR - tt) / 0.9, 0, 1)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.3)
mix = mix / np.max(np.abs(mix)) * 0.89
mix = mix[:, :int(TOTAL * SR)]
inter = (mix.T * 32767).astype(np.int16)
w = wave.open('music2.wav', 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(inter.tobytes()); w.close()
print("ok", mix.shape[1] / SR)
