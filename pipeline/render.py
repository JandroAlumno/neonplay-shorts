import sys, math, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FB = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
WHITE = (255, 255, 255); PINK = (255, 79, 163); ORANGE = (255, 160, 60); CYAN = (70, 230, 255); YEL = (255, 225, 80)

# (duration, label, [(text, size, color)], sub)
SCENES = [
    (3.6, "ATENCIÓN", [("GTA 6", 230, PINK), ("SALE EN", 120, WHITE), ("2 DÍAS", 210, YEL)], "esto es lo que tienes que saber"),
    (3.4, "LA FECHA", [("JUEVES", 120, WHITE), ("19", 380, PINK), ("NOVIEMBRE", 120, WHITE)], "confirmada por Rockstar"),
    (3.6, "DÓNDE JUGAR", [("PS5", 200, CYAN), ("y", 90, WHITE), ("XBOX", 200, CYAN), ("SERIES X|S", 110, CYAN)], "PC: todavía sin fecha"),
    (3.4, "YA PUEDES", [("PRE-", 190, WHITE), ("CARGARLO", 160, ORANGE)], "la precarga abrió el 12 de noviembre"),
    (3.4, "EL MAPA", [("VUELVE", 140, WHITE), ("VICE", 250, PINK), ("CITY", 250, PINK)], "en el estado de Leonida"),
    (3.4, "PROTAGONISTAS", [("JASON", 200, CYAN), ("&", 130, WHITE), ("LUCÍA", 200, PINK)], "dos personajes jugables"),
    (3.8, "SE HIZO ESPERAR", [("2025", 150, (150,150,170)), ("MAYO 2026", 130, (150,150,170)), ("19 NOV 2026", 140, YEL)], "dos retrasos hasta la fecha final"),
    (3.6, "¿LO VAS A JUGAR EL DÍA 1?", [("SÍGUEME", 170, WHITE), ("PARA TODO", 130, WHITE), ("GTA 6", 230, PINK)], "trucos, secretos y noticias"),
]
TOTAL = sum(s[0] for s in SCENES)

def base_bg():
    y = np.linspace(0, 1, H)[:, None]
    top = np.array([14, 6, 30]); mid = np.array([70, 14, 90]); hor = np.array([255, 90, 120])
    hy = 0.62
    a = np.clip(y / hy, 0, 1)
    col = np.where(y < hy, top + (mid - top) * a ** 1.4, 0)
    col = col + np.where(y < hy, (hor - mid) * np.clip((y - 0.45) / (hy - 0.45), 0, 1) ** 2, 0)
    ground = np.array([10, 4, 22])
    col = np.where(y >= hy, ground, col)
    img = np.broadcast_to(col[:, None, :] if col.ndim == 2 else col, (H, W, 3)).astype(np.uint8).copy()
    im = Image.fromarray(img)
    # sun
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sun)
    cx, cy, r = W // 2, int(H * hy) - 40, 300
    for i in range(r * 2):
        yy = cy - r + i
        t = i / (2 * r)
        c = (int(255), int(220 - 150 * t), int(90 + 60 * t), 255)
        half = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
        if t > 0.5 and int((t - 0.5) * 40) % 3 == 0:  # stripes
            continue
        d.line([(cx - half, yy), (cx + half, yy)], fill=c)
    sun = sun.crop((0, 0, W, int(H * hy)))
    glow = sun.filter(ImageFilter.GaussianBlur(60))
    im.paste(glow, (0, 0), glow); im.paste(sun, (0, 0), sun)
    return im, int(H * hy)

BG, HY = base_bg()

def grid(im, t):
    d = ImageDraw.Draw(im)
    vx = W / 2
    for i in range(-8, 9):
        d.line([(vx + i * 40, HY), (vx + i * 420, H)], fill=(255, 70, 170), width=3)
    off = (t * 0.8) % 1
    for k in range(14):
        z = (k + off) / 14
        yy = HY + (H - HY) * z ** 2.2
        d.line([(0, yy), (W, yy)], fill=(255, 70, 170), width=3)

def text_layer(scene):
    dur, label, lines, sub = scene
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    sizes = []
    for txt, sz, col in lines:
        f = ImageFont.truetype(FB, sz)
        while d.textlength(txt, font=f) > W - 110:
            sz -= 6; f = ImageFont.truetype(FB, sz)
        bb = d.textbbox((0, 0), txt, font=f)
        sizes.append((txt, f, col, bb))
    gap = 18
    total = sum(b[3] - b[1] for *_, b in sizes) + gap * (len(sizes) - 1)
    y = int(H * 0.40 - total / 2)
    out = []
    for txt, f, col, bb in sizes:
        w = bb[2] - bb[0]; h = bb[3] - bb[1]
        out.append((txt, f, col, ((W - w) // 2 - bb[0], y - bb[1]), (y, y + h)))
        y += h + gap
    # dark plate
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate)
    y0 = out[0][4][0] - 150; y1 = out[-1][4][1] + 190
    pd.rounded_rectangle([40, y0, W - 40, y1], radius=50, fill=(8, 2, 20, 170))
    layer.alpha_composite(plate)
    # label pill
    lf = ImageFont.truetype(FX, 46)
    lw = d.textlength(label, font=lf)
    d.rounded_rectangle([(W - lw) / 2 - 34, y0 - 40, (W + lw) / 2 + 34, y0 + 40], radius=40, fill=PINK)
    d.text((W / 2, y0), label, font=lf, fill=WHITE, anchor="mm")
    for txt, f, col, pos, _ in out:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        sd.text(pos, txt, font=f, fill=col + (255,))
        glow = sh.filter(ImageFilter.GaussianBlur(18))
        layer.alpha_composite(glow); layer.alpha_composite(glow)
        d.text((pos[0] + 6, pos[1] + 8), txt, font=f, fill=(0, 0, 0, 200))
        d.text(pos, txt, font=f, fill=col)
    sf = ImageFont.truetype(FX, 54)
    d.text((W / 2, y1 - 85), sub, font=sf, fill=(255, 255, 255, 235), anchor="mm")
    return layer

def ease(x): return 1 - (1 - min(max(x, 0), 1)) ** 3

def frame(i_scene, layer, t, gt):
    im = BG.copy(); grid(im, gt); im = im.convert("RGBA")
    dur = SCENES[i_scene][0]
    p = ease(t / 0.35)
    s = 0.82 + 0.18 * p + 0.025 * (t / dur)  # pop + slow push
    a = min(t / 0.2, 1) * min((dur - t) / 0.18, 1)
    if abs(s - 1) > 0.002:
        lw, lh = int(W * s), int(H * s)
        l2 = layer.resize((lw, lh), Image.BILINEAR)
        l = Image.new("RGBA", (W, H), (0, 0, 0, 0)); l.paste(l2, ((W - lw) // 2, (H - lh) // 2))
    else:
        l = layer
    if a < 1:
        al = l.getchannel("A").point(lambda v: int(v * max(a, 0)))
        l = l.copy(); l.putalpha(al)
    im.alpha_composite(l)
    d = ImageDraw.Draw(im)
    # progress bar
    d.rectangle([0, 0, W, 16], fill=(0, 0, 0, 160))
    d.rectangle([0, 0, int(W * gt / TOTAL), 16], fill=YEL)
    # flash at scene start
    if t < 0.08:
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(120 * (1 - t / 0.08))))
        im.alpha_composite(fl)
    return im.convert("RGB")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "test":
        for i in [0, 1, 6, 7]:
            frame(i, text_layer(SCENES[i]), 1.5, 2.0).save(f"test{i}.jpg", quality=88)
    else:
        gstart = 0
        for i, sc in enumerate(SCENES):
            dur = sc[0]; n = round(dur * FPS); layer = text_layer(sc)
            tmp = f"part{i}.tmp.mp4"
            p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                  "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
            for k in range(n):
                t = k / FPS
                p.stdin.write(frame(i, layer, t, gstart + t).tobytes())
            p.stdin.close()
            if p.wait() == 0: os.rename(tmp, f"part{i}.mp4")
            gstart += n / FPS
            print("scene", i, "done", flush=True)
