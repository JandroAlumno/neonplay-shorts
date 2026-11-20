import sys, math, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from timing import *
import render as r1  # reuse background + scene texts + colors
T = r1.T

W, H = 1080, 1920
SCENES = r1.SCENES
BG, HY = r1.BG, r1.HY
FB, FX = r1.FB, r1.FX
rng = np.random.default_rng(3)

def make_el(txt, font, col, glow=True):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bb = d0.textbbox((0, 0), txt, font=font)
    pad = 50
    w, h = bb[2] - bb[0] + pad * 2, bb[3] - bb[1] + pad * 2
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pos = (pad - bb[0], pad - bb[1])
    if glow:
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(g).text(pos, txt, font=font, fill=col + (255,))
        g = g.filter(ImageFilter.GaussianBlur(16)); im.alpha_composite(g); im.alpha_composite(g)
    d.text((pos[0] + 6, pos[1] + 8), txt, font=font, fill=(0, 0, 0, 200))
    d.text(pos, txt, font=font, fill=col)
    return im, bb[3] - bb[1]

def build_outro():
    av = Image.open("assets/avatar.png").convert("RGBA").resize((560, 560))
    mask = Image.new("L", (560, 560), 0); ImageDraw.Draw(mask).ellipse([0, 0, 559, 559], fill=255)
    pad = 90; size = 560 + pad * 2
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([pad - 22, pad - 22, pad + 582, pad + 582], fill=T["accent"] + (255,))
    glow = ring.filter(ImageFilter.GaussianBlur(26)); im.alpha_composite(glow); im.alpha_composite(ring)
    im.paste(av, (pad, pad), mask)
    t1, _ = make_el("SÍGUEME", ImageFont.truetype(FB, 190), r1.WHITE)
    t2, _ = make_el("@neonplaycanal", ImageFont.truetype(FB, 84), T["accent"])
    subim, _ = make_el("noticias y trucos gamer cada día", ImageFont.truetype(FX, 54), (255, 255, 255), glow=False)
    y0, y1 = 280, 1480
    plate = Image.new("RGBA", (W - 80, y1 - y0), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, plate.width - 1, plate.height - 1], radius=T["radius"], fill=T["plate"] + (175,))
    lf = ImageFont.truetype(FX, 46); lw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength("NO TE LO PIERDAS", font=lf)
    pill = Image.new("RGBA", (int(lw + 68), 80), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill.width - 1, 79], radius=min(40, T["radius"]), fill=T["accent"])
    pd.text((pill.width / 2, 40), "NO TE LO PIERDAS", font=lf, fill=r1.WHITE, anchor="mm")
    return [(plate, W / 2, (y0 + y1) / 2, -0.01, "plate"), (pill, W / 2, y0, 0, "drop"),
            (im, W / 2, 700, 0, "pop"), (t1, W / 2, 1140, 1, "pop"), (t2, W / 2, 1290, 2, "pop"), (subim, W / 2, 1400, 3, "rise")]

def build(scene):
    if scene is None:
        return build_outro()
    dur, label, lines, sub = scene
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    items = []
    for txt, sz, col in lines:
        f = ImageFont.truetype(FB, sz)
        while d0.textlength(txt, font=f) > W - 110:
            sz -= 6; f = ImageFont.truetype(FB, sz)
        items.append(make_el(txt, f, col))
    gap = 18
    total = sum(h for _, h in items) + gap * (len(items) - 1)
    y = H * T["ypos"] - total / 2
    els = []  # (img, cx, cy, appear_beat, kind)
    for k, (im, h) in enumerate(items):
        els.append((im, W / 2, y + h / 2, k, "pop"))
        y += h + gap
    y0 = els[0][2] - items[0][1] / 2 - 150; y1 = y - gap + 190
    plate = Image.new("RGBA", (W - 80, int(y1 - y0)), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, plate.width - 1, plate.height - 1], radius=T["radius"], fill=T["plate"] + (175,))
    lf = ImageFont.truetype(FX, 46); lw = d0.textlength(label, font=lf)
    pill = Image.new("RGBA", (int(lw + 68), 80), (0, 0, 0, 0)); pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill.width - 1, 79], radius=min(40, T["radius"]), fill=T["accent"])
    pd.text((pill.width / 2, 40), label, font=lf, fill=r1.WHITE, anchor="mm")
    subim, _ = make_el(sub, ImageFont.truetype(FX, 54), (255, 255, 255), glow=False)
    pre = [(plate, W / 2, (y0 + y1) / 2, -0.01, "plate"), (pill, W / 2, y0, 0, "drop")]
    post = [(subim, W / 2, y1 - 85, len(lines), "rise")]
    return pre + els + post

def back(x):  # ease out back
    c = 1.9; x = min(max(x, 0), 1)
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def place(canvas, im, cx, cy, s, a, dy=0):
    if a <= 0.01 or s <= 0.02: return
    if abs(s - 1) > 0.004:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if a < 0.999:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2 + dy)))

def grid(im, gt, pulse):
    d = ImageDraw.Draw(im); vx = W / 2
    g0 = T["grid"]; c = tuple(min(255, int(g0[k] + (255 - g0[k]) * 0.55 * pulse)) for k in range(3))
    for i in range(-8, 9):
        d.line([(vx + i * 40, HY), (vx + i * 420, H)], fill=c, width=3)
    off = (gt / BEAT) % 1
    for k in range(14):
        z = (k + off) / 14; yy = HY + (H - HY) * z ** 2.2
        d.line([(0, yy), (W, yy)], fill=c, width=3 + int(3 * pulse * z))

def frame(sc_i, els, t, gt):
    beat_pos = gt / BEAT
    phase = beat_pos % 1
    pulse = math.exp(-phase * 6)
    sdur = BEATS_PER_SCENE * BEAT
    big = sc_i in BIG
    im = BG.copy(); grid(im, gt, pulse); im = im.convert("RGBA")
    out_p = max(0, (t - (sdur - 0.5 * BEAT)) / (0.5 * BEAT)) if sc_i < N_SCENES - 1 else 0
    for img, cx, cy, ab, kind in els:
        lt = t - ab * BEAT
        if lt < 0: continue
        p = lt / 0.2
        if kind == "pop": s, a, dy = 0.4 + 0.6 * back(p), min(p * 2, 1), 0
        elif kind == "drop": s, a, dy = 1, min(p * 2, 1), -80 * (1 - back(p))
        elif kind == "rise": s, a, dy = 1, min(p, 1), 60 * (1 - back(p))
        else: s, a, dy = 0.9 + 0.1 * back(lt / 0.15), min(lt / 0.1, 1), 0
        if kind == "pop":
            s *= 1 + 0.04 * pulse  # breathe on every kick
        if out_p > 0:
            s *= 1 + 0.5 * out_p; a *= 1 - out_p
        place(im, img, cx, cy, s, a, dy)
    # camera punch + shake
    z = 1 + 0.018 * pulse + (0.07 if big else 0.04) * math.exp(-t * 10)
    sh = (24 if big else 12) * math.exp(-t * 14)
    ox, oy = rng.uniform(-sh, sh), rng.uniform(-sh, sh)
    if z > 1.002 or sh > 0.5:
        zw, zh = int(W * z), int(H * z)
        im = im.resize((zw, zh), Image.BILINEAR)
        l = int((zw - W) / 2 + ox); tp = int((zh - H) / 2 + oy)
        l = min(max(l, 0), zw - W); tp = min(max(tp, 0), zh - H)
        im = im.crop((l, tp, l + W, tp + H))
    arr = np.asarray(im.convert("RGB")).copy()
    # glitch on cut in/out
    g = max(math.exp(-t * 18) if t < 0.2 else 0, out_p ** 2)
    if g > 0.05:
        sft = int(30 * g)
        arr[:, :, 0] = np.roll(arr[:, :, 0], sft, axis=1); arr[:, :, 2] = np.roll(arr[:, :, 2], -sft, axis=1)
        for _ in range(int(6 * g)):
            y = rng.integers(0, H - 60); hh = rng.integers(10, 60)
            arr[y:y + hh] = np.roll(arr[y:y + hh], rng.integers(-60, 60), axis=1)
    # white flash on cut
    fl = (0.55 if big else 0.3) * max(0, 1 - t / 0.07)
    if fl > 0: arr = (arr * (1 - fl) + 255 * fl).astype(np.uint8)
    # progress bar
    arr[0:16] = (arr[0:16] * 0.35).astype(np.uint8)
    arr[0:16, :int(W * min(gt / TOTAL, 1))] = T["bar"]
    return arr

def scene_bounds(i):
    st = i * BEATS_PER_SCENE * BEAT
    en = (i + 1) * BEATS_PER_SCENE * BEAT if i < N_SCENES - 1 else TOTAL
    return st, en

if __name__ == "__main__":
    if sys.argv[1] == "test":
        outs = []
        for i, t in [(0, 0.05), (0, 1.4), (6, 3.3), (8, 2.2)]:
            els = build((SCENES + [None])[i]); st, _ = scene_bounds(i)
            outs.append(Image.fromarray(frame(i, els, t, st + t)).resize((540, 960)))
        g = Image.new("RGB", (2160, 960)); [g.paste(o, (k * 540, 0)) for k, o in enumerate(outs)]; g.save("test2.jpg", quality=85)
    else:
        f0 = 0
        for i in range(N_SCENES):
            st, en = scene_bounds(i)
            f1 = round(en * FPS); nfr = f1 - f0
            els = build((SCENES + [None])[i]); tmp = f"p2_{i}.tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                  "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for k in range(nfr):
                gt = (f0 + k) / FPS
                p.stdin.write(frame(i, els, gt - st, gt).tobytes())
            p.stdin.close()
            if p.wait() == 0: os.rename(tmp, f"p2_{i}.mp4")
            f0 = f1
            print("scene", i, flush=True)
