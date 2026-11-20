#!/bin/bash
# Uso: pipeline/make_short.sh <carpeta_trabajo> <scenes.py> <salida.mp4>
# scenes.py define SCENES (8 escenas) y VOICE (9 frases: 8 escenas + cierre). Opcional: CHORDS, SEED, VOICE_NAME, VOICE_SPEED.
set -e
W="$1"; SC="$2"; OUT="$3"; P="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$W"; cp "$P"/*.py "$W"/; cp -r "$P"/assets "$W"/; cp "$SC" "$W/scenes.py"
# voz gratuita (Kokoro): dependencias y modelo, una sola vez
python3 -c "import kokoro_onnx, soundfile" 2>/dev/null || pip install --break-system-packages -q kokoro-onnx soundfile
export KOKORO_DIR="${KOKORO_DIR:-$HOME/.cache/neonplay}"; mkdir -p "$KOKORO_DIR"
R=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -s "$KOKORO_DIR/kokoro.onnx" ] || curl -sSL -m 280 -o "$KOKORO_DIR/kokoro.onnx" $R/kokoro-v1.0.int8.onnx
[ -s "$KOKORO_DIR/voices.bin" ] || curl -sSL -m 120 -o "$KOKORO_DIR/voices.bin" $R/voices-v1.0.bin
cd "$W"
python3 - <<'PY'
s=open('render.py').read()
a=s.index('SCENES = ['); b=s.index('TOTAL = sum')
s=s[:a]+'from scenes import SCENES\n'+s[b:]
open('render.py','w').write(s)
m=open('music2.py').read()
m=m.replace("chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]",
 "import scenes as _sc\nchords = getattr(_sc, 'CHORDS', [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)])")
m=m.replace("rng = np.random.default_rng(7)","import scenes as _s0\nrng = np.random.default_rng(getattr(_s0, 'SEED', 7))")
open('music2.py','w').write(m)
PY
python3 music2.py >/dev/null
python3 voice.py
python3 render2.py test
python3 render2.py full >/dev/null
ls p2_*.mp4 | sort -V | sed "s/^/file '/;s/$/'/" > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy video.mp4
ffmpeg -v error -y -i video.mp4 -i final.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT"
ffmpeg -v error -y -i "$OUT" -vf "fps=1/3.5,scale=240:-1,tile=9x1" -frames:v 1 "${OUT%.mp4}_check.jpg"
ffmpeg -nostats -i "$OUT" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
echo "OK $OUT"
