"""Genera la voz en off (Kokoro, gratis) alineada con las escenas y la mezcla con la música.

Entrada (en el directorio de trabajo): scenes.py con VOICE (una frase por escena, 9 en total:
8 escenas + la escena final con el avatar) y music2.wav. Opcionales en scenes.py:
VOICE_NAME (em_alex, em_santa) y VOICE_SPEED (1.05 por defecto).
Salida: final.wav (música con ducking + voz).
"""
import os, sys, wave
import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import maximum_filter1d
from timing import *
import scenes as S

VOICE = list(getattr(S, "VOICE", []))
if len(VOICE) != N_SCENES:
    sys.exit(f"ERROR: scenes.py necesita VOICE con {N_SCENES} frases (una por escena, la última para el cierre); tiene {len(VOICE)}")
NAME = getattr(S, "VOICE_NAME", "em_alex")
BASE = float(getattr(S, "VOICE_SPEED", 1.35))
D = os.environ.get("KOKORO_DIR", os.path.expanduser("~/.cache/neonplay"))

from kokoro_onnx import Kokoro
k = Kokoro(os.path.join(D, "kokoro.onnx"), os.path.join(D, "voices.bin"))

def synth(text, speed):
    s, sr = k.create(text, voice=NAME, speed=speed, lang="es")
    assert sr == 24000, sr
    s = np.asarray(s, dtype=np.float32)
    idx = np.where(np.abs(s) > 0.01 * max(np.max(np.abs(s)), 1e-6))[0]
    s = s[max(idx[0] - int(0.02 * sr), 0): idx[-1] + int(0.05 * sr)]
    return s, sr

OFFSET = 0.18  # la voz entra justo después del golpe de cada escena
track = np.zeros(int(TOTAL * SR) + SR, dtype=np.float32)
for i, text in enumerate(VOICE):
    st = i * BEATS_PER_SCENE * BEAT + OFFSET
    last = i == N_SCENES - 1
    end = TOTAL - 0.5 if last else (i + 1) * BEATS_PER_SCENE * BEAT - 0.25
    maxd = end - st
    speed = BASE
    for _ in range(3):
        s, sr = synth(text, speed)
        d = len(s) / sr
        if d <= maxd:
            break
        speed = min(1.4, speed * d / maxd * 1.02)
    if d > maxd:
        print(f"AVISO escena {i}: la frase dura {d:.2f}s y solo caben {maxd:.2f}s; se recorta. Acórtala.", flush=True)
        s = s[: int(maxd * sr)]
        s[-int(0.08 * sr):] *= np.linspace(1, 0, int(0.08 * sr))
    v = signal.resample_poly(s, 147, 80)  # 24 kHz -> 44,1 kHz
    v = v / max(np.max(np.abs(v)), 1e-6) * 0.9
    a = int(st * SR)
    track[a:a + len(v)] += v[: len(track) - a]
    print(f"escena {i}: {len(s)/sr:.2f}s de {maxd:.2f}s (velocidad {speed:.2f})  {text}", flush=True)

w = wave.open("music2.wav")
m = np.frombuffer(w.readframes(w.getnframes()), np.int16).reshape(-1, 2).astype(np.float32) / 32767
n = min(len(m), len(track))
m, v = m[:n], track[:n]
env = maximum_filter1d(np.abs(v), size=int(0.08 * SR))
env = signal.sosfilt(signal.butter(1, 8, "low", fs=SR, output="sos"), env)
env = np.clip(env / 0.12, 0, 1)
duck = 1 - 0.62 * env  # la música baja mientras habla
mix = m * 0.8 * duck[:, None] + v[:, None]
mix = np.tanh(mix * 0.95) / np.tanh(0.95)
mix = mix / max(np.max(np.abs(mix)), 1e-6) * 0.92
out = wave.open("final.wav", "wb"); out.setnchannels(2); out.setsampwidth(2); out.setframerate(SR)
out.writeframes((mix * 32767).astype(np.int16).tobytes()); out.close()
print("OK final.wav", round(n / SR, 2), "s")
