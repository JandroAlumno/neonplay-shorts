# Ejemplo de scenes.py. Colores: WHITE, PINK, ORANGE, CYAN, YEL o tuplas RGB.
WHITE=(255,255,255); PINK=(255,79,163); ORANGE=(255,160,60); CYAN=(70,230,255); YEL=(255,225,80)
# Opcional: acordes (notas MIDI) y semilla para variar la música
CHORDS = [(57,60,64),(53,57,60),(48,52,55),(55,59,62)]
SEED = 7
# 8 escenas: (duración_ignorada, ETIQUETA, [(texto, tamaño, color), ...], subtítulo)
SCENES = [
    (3.4, "ATENCIÓN", [("GTA 6", 230, PINK), ("SALE EN", 120, WHITE), ("2 DÍAS", 210, YEL)], "esto es lo que tienes que saber"),
    (3.4, "LA FECHA", [("JUEVES", 120, WHITE), ("19", 380, PINK), ("NOVIEMBRE", 120, WHITE)], "confirmada por Rockstar"),
    (3.4, "DÓNDE JUGAR", [("PS5", 200, CYAN), ("y", 90, WHITE), ("XBOX", 200, CYAN), ("SERIES X|S", 110, CYAN)], "PC: todavía sin fecha"),
    (3.4, "YA PUEDES", [("PRE-", 190, WHITE), ("CARGARLO", 160, ORANGE)], "la precarga abrió el 12 de noviembre"),
    (3.4, "EL MAPA", [("VUELVE", 140, WHITE), ("VICE", 250, PINK), ("CITY", 250, PINK)], "en el estado de Leonida"),
    (3.4, "PROTAGONISTAS", [("JASON", 200, CYAN), ("&", 130, WHITE), ("LUCÍA", 200, PINK)], "dos personajes jugables"),
    (3.4, "SE HIZO ESPERAR", [("2025", 150, (150,150,170)), ("MAYO 2026", 130, (150,150,170)), ("19 NOV 2026", 140, YEL)], "dos retrasos hasta la fecha final"),
    (3.4, "¿LO VAS A JUGAR EL DÍA 1?", [("SÍGUEME", 170, WHITE), ("PARA TODO", 130, WHITE), ("GTA 6", 230, PINK)], "trucos, secretos y noticias"),
]
