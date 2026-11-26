#!/usr/bin/env python3
"""Sube un Short a NEON PLAY con la API oficial de YouTube (solo librería estándar).

Uso: python3 pipeline/yt_upload.py uploads/<nombre>.json
Manifiesto: {"video", "title", "description", "tags": [], "publishAt": "ISO 8601 opcional"}
Credenciales (solo por variables de entorno): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

CHANNEL_ID = "UCDssxtaqOIDadQCc0dzT8sg"  # NEON PLAY


def call(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.headers, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR HTTP {e.code}: {e.read().decode(errors='replace')[:800]}")


def main(path):
    with open(path, encoding="utf-8") as f:
        m = json.load(f)
    form = urllib.parse.urlencode({
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    _, tok = call(urllib.request.Request("https://oauth2.googleapis.com/token", data=form))
    auth = {"Authorization": f"Bearer {tok['access_token']}"}

    # Nunca subir a otra cuenta (p. ej. la personal)
    _, ch = call(urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/channels?part=id&mine=true", headers=auth))
    if [c["id"] for c in ch.get("items", [])] != [CHANNEL_ID]:
        sys.exit("ERROR: el token no es del canal NEON PLAY. No se sube nada.")

    status = {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
              "containsSyntheticMedia": True}
    if m.get("publishAt"):  # programado: privado hasta publishAt
        status.update(privacyStatus="private", publishAt=m["publishAt"])
    body = json.dumps({
        "snippet": {"title": m["title"], "description": m["description"],
                    "tags": m.get("tags", []), "categoryId": "20",
                    "defaultLanguage": "es"},
        "status": status,
    }).encode()
    with open(m["video"], "rb") as f:
        data = f.read()
    headers, _ = call(urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=body, headers={**auth, "Content-Type": "application/json; charset=UTF-8",
                            "X-Upload-Content-Type": "video/mp4",
                            "X-Upload-Content-Length": str(len(data))}))
    _, res = call(urllib.request.Request(
        headers["Location"], data=data, method="PUT",
        headers={**auth, "Content-Type": "video/mp4"}))
    st = res.get("status", {})
    print(f"SUBIDO https://youtube.com/shorts/{res['id']}")
    print("privacidad:", st.get("privacyStatus"), "| publishAt:", st.get("publishAt"),
          "| contenido sintético:", st.get("containsSyntheticMedia"))


if __name__ == "__main__":
    main(sys.argv[1])
