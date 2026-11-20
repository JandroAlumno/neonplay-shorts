"""Temas visuales de los Shorts. scenes.py puede definir THEME = "<nombre>" (por defecto "synthwave").
Cada tema cambia: colores del fondo, sol/luna, rejilla, tipografía, forma de la placa y posición del texto.
Los colores de cada línea de texto los sigue eligiendo scenes.py (úsalos en armonía con el tema)."""
import os

_INTER = "/usr/share/fonts/opentype/inter/"
_POP = "/usr/share/fonts/truetype/google-fonts/"

def _font(*names):
    for n in names:
        for d in (_INTER, _POP):
            if os.path.exists(d + n):
                return d + n
    return _INTER + "Inter-Black.otf"

THEMES = {
    "synthwave": dict(top=(14, 6, 30), mid=(70, 14, 90), hor=(255, 90, 120), ground=(10, 4, 22), sun="sun",
                      sun_top=(255, 220, 90), sun_bot=(255, 70, 150), grid=(255, 70, 170), accent=(255, 79, 163), bar=(255, 225, 80),
                      plate=(8, 2, 20), radius=50, ypos=0.40, fb=_font("Inter-Black.otf"), fx=_font("Inter-ExtraBold.otf")),
    "ocean": dict(top=(3, 12, 36), mid=(6, 58, 112), hor=(0, 200, 220), ground=(2, 10, 28), sun="moon",
                  sun_top=(235, 255, 255), sun_bot=(150, 235, 255), grid=(60, 220, 255), accent=(0, 190, 255), bar=(120, 255, 235),
                  plate=(2, 12, 30), radius=70, ypos=0.42, fb=_font("Poppins-Bold.ttf", "Inter-Black.otf"), fx=_font("Poppins-Medium.ttf", "Inter-ExtraBold.otf")),
    "lava": dict(top=(24, 4, 4), mid=(100, 18, 8), hor=(255, 140, 30), ground=(18, 4, 4), sun="sun",
                 sun_top=(255, 235, 120), sun_bot=(255, 60, 20), grid=(255, 120, 40), accent=(255, 110, 30), bar=(255, 200, 60),
                 plate=(20, 4, 2), radius=14, ypos=0.38, fb=_font("Inter-BlackItalic.otf", "Inter-Black.otf"), fx=_font("Inter-ExtraBoldItalic.otf", "Inter-ExtraBold.otf")),
    "matrix": dict(top=(2, 14, 8), mid=(6, 62, 32), hor=(110, 255, 130), ground=(2, 10, 6), sun="none",
                   sun_top=(0, 0, 0), sun_bot=(0, 0, 0), grid=(60, 255, 140), accent=(70, 255, 130), bar=(180, 255, 90),
                   plate=(0, 10, 4), radius=6, ypos=0.45, fb=_font("Inter-ExtraBold.otf", "Inter-Black.otf"), fx=_font("Inter-Medium.otf", "Inter-ExtraBold.otf")),
    "candy": dict(top=(44, 12, 78), mid=(150, 52, 172), hor=(255, 172, 224), ground=(30, 8, 52), sun="sun",
                  sun_top=(255, 250, 200), sun_bot=(255, 130, 210), grid=(255, 190, 240), accent=(255, 120, 210), bar=(255, 240, 150),
                  plate=(30, 6, 50), radius=80, ypos=0.41, fb=_font("Poppins-Bold.ttf", "Inter-Black.otf"), fx=_font("Poppins-Regular.ttf", "Inter-ExtraBold.otf")),
    "midnight": dict(top=(6, 6, 14), mid=(26, 28, 56), hor=(120, 132, 210), ground=(5, 5, 12), sun="moon",
                     sun_top=(245, 245, 255), sun_bot=(190, 195, 235), grid=(120, 140, 255), accent=(110, 130, 255), bar=(190, 200, 255),
                     plate=(4, 4, 12), radius=30, ypos=0.43, fb=_font("Inter-Black.otf"), fx=_font("Inter-SemiBold.otf", "Inter-ExtraBold.otf")),
}

def get():
    try:
        import scenes
        name = getattr(scenes, "THEME", "synthwave")
    except Exception:
        name = "synthwave"
    return THEMES.get(name, THEMES["synthwave"])
