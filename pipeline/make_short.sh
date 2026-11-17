#!/bin/bash
# Uso: pipeline/make_short.sh <carpeta_trabajo> <scenes.py> <salida.mp4>
# scenes.py debe definir SCENES (8 escenas). Opcional: CHORDS y SEED para variar la música.
set -e
W="$1"; SC="$2"; OUT="$3"; P="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$W"; cp "$P"/{render.py,render2.py,timing.py,music2.py} "$W"/; cp "$SC" "$W/scenes.py"
cd "$W"
python3 - <<'PY'
import re
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
python3 render2.py test
python3 render2.py full >/dev/null
ls p2_*.mp4 | sort -V | sed "s/^/file '/;s/$/'/" > list.txt
ffmpeg -v error -y -f concat -safe 0 -i list.txt -c copy video.mp4
ffmpeg -v error -y -i video.mp4 -i music2.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest "$OUT"
ffmpeg -v error -y -i "$OUT" -vf "fps=1/3.5,scale=270:-1,tile=8x1" -frames:v 1 "${OUT%.mp4}_check.jpg"
echo "OK $OUT"
