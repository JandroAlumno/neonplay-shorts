#!/usr/bin/env python3
"""Detector de temas virales para NEON PLAY (solo lee metadatos públicos).

Qué hace: consulta fuentes oficiales/públicas y devuelve una lista ordenada de TEMAS
candidatos (título + métrica + enlace). NO descarga vídeos, imágenes ni audio de nadie:
solo guarda títulos, cifras y URLs. Con cada tema se hace después un Short ORIGINAL
(guion propio, voz propia, datos verificados en 2 fuentes).

Fuentes (cada una falla en silencio si no hay red o clave):
  youtube : YouTube Data API v3 (chart=mostPopular, categoría Gaming). Requiere YOUTUBE_API_KEY.
  reddit  : JSON público de subreddits gamer (puntuación y comentarios).
  steam   : API pública de la tienda de Steam (más vendidos, novedades, ofertas).
  trends  : RSS de tendencias de Google (España).

Uso:  python3 trends.py [--min-views 100000] [--top 15] [--out trends.json]
      python3 trends.py --selftest
"""
import argparse, json, os, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "neonplay-trends/1.0 (lectura de metadatos públicos)"}
SUBS = ["gaming", "Games", "pcgaming", "NintendoSwitch", "PS5", "xbox", "Steam", "fortnite"]

def get(url, timeout=15):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()

def youtube(min_views):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        return []
    out = []
    for region in ("ES", "US"):
        q = urllib.parse.urlencode({"part": "snippet,statistics", "chart": "mostPopular", "videoCategoryId": "20",
                                    "regionCode": region, "maxResults": 25, "key": key})
        for it in json.loads(get("https://www.googleapis.com/youtube/v3/videos?" + q)).get("items", []):
            v = int(it["statistics"].get("viewCount", 0))
            if v >= min_views:
                out.append({"source": f"youtube-{region}", "title": it["snippet"]["title"], "metric": "vistas",
                            "value": v, "url": "https://youtu.be/" + it["id"]})
    return out

def reddit(_):
    out = []
    for s in SUBS:
        d = json.loads(get(f"https://www.reddit.com/r/{s}/top.json?t=day&limit=10"))
        for c in d["data"]["children"]:
            p = c["data"]
            out.append({"source": f"reddit-r/{s}", "title": p["title"], "metric": "votos",
                        "value": p["score"], "url": "https://reddit.com" + p["permalink"]})
    return out

def steam(_):
    d = json.loads(get("https://store.steampowered.com/api/featuredcategories?cc=es&l=spanish"))
    out = []
    for cat, label in (("top_sellers", "más vendido"), ("new_releases", "novedad"), ("specials", "oferta")):
        for i, g in enumerate(d.get(cat, {}).get("items", [])[:10]):
            out.append({"source": f"steam-{cat}", "title": g["name"], "metric": label,
                        "value": 10 - i, "url": f"https://store.steampowered.com/app/{g['id']}"})
    return out

def trends(_):
    root = ET.fromstring(get("https://trends.google.com/trending/rss?geo=ES"))
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for it in root.iter("item"):
        t = it.findtext("title"); tr = it.findtext("ht:approx_traffic", namespaces=ns) or "0"
        out.append({"source": "google-trends-ES", "title": t, "metric": "búsquedas",
                    "value": int(tr.replace("+", "").replace(",", "") or 0), "url": it.findtext("link") or ""})
    return out

SOURCES = {"youtube": youtube, "reddit": reddit, "steam": steam, "trends": trends}

def rank(items, top):
    # puntuación relativa dentro de cada fuente (0-1) y suma entre fuentes si el tema coincide
    by_src = {}
    for it in items: by_src.setdefault(it["source"].split("-")[0], []).append(it)
    for lst in by_src.values():
        m = max(x["value"] for x in lst) or 1
        for x in lst: x["score"] = round(x["value"] / m, 3)
    merged = {}
    for it in items:
        k = " ".join(sorted(set(it["title"].lower().split()))[:6])
        e = merged.setdefault(k, {"title": it["title"], "score": 0, "sources": []})
        e["score"] += it["score"]; e["sources"].append({k2: it[k2] for k2 in ("source", "metric", "value", "url")})
    res = sorted(merged.values(), key=lambda e: (len(e["sources"]), e["score"]), reverse=True)
    for e in res: e["score"] = round(e["score"], 3)
    return res[:top]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-views", type=int, default=100000)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--out", default="trends.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        items = [{"source": "youtube-ES", "title": "Nuevo parche de Fortnite", "metric": "vistas", "value": 250000, "url": "u1"},
                 {"source": "reddit-r/Fortnite", "title": "Nuevo parche de Fortnite", "metric": "votos", "value": 900, "url": "u2"},
                 {"source": "steam-top_sellers", "title": "Juego X", "metric": "más vendido", "value": 10, "url": "u3"}]
        r = rank(items, 5); assert r[0]["title"] == "Nuevo parche de Fortnite" and len(r[0]["sources"]) == 2
        print("selftest OK"); return
    items, errores = [], []
    for name, fn in SOURCES.items():
        try: items += fn(a.min_views)
        except Exception as e: errores.append(f"{name}: {type(e).__name__}: {e}")
    res = rank(items, a.top) if items else []
    json.dump({"temas": res, "fuentes_con_error": errores}, open(a.out, "w"), ensure_ascii=False, indent=1)
    for e in res: print(f"{e['score']:>5}  {e['title']}  ({len(e['sources'])} fuentes)")
    for e in errores: print("AVISO", e, file=sys.stderr)

if __name__ == "__main__":
    main()
