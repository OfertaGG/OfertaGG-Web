#!/usr/bin/env python3
"""
OfertaGG - descubrir juegos nuevos (cada día, antes de update.py).

Mira en Steam (España) los más vendidos, las novedades populares y los próximos
lanzamientos más esperados, y añade a config/juegos.json los que aún no estén.
Solo juegos de pago (nada de DLC, bandas sonoras, programas ni juegos gratis) y
con público de verdad, para que la web crezca con juegos que la gente busca.

  python scripts/descubrir.py            -> añade como mucho 25 juegos
  python scripts/descubrir.py 400        -> añade como mucho 400 (ampliación grande)

Los juegos NUNCA se borran solos: si quieres quitar uno, bórralo de config/juegos.json.
"""
import json, os, re, sys, time, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "config", "juegos.json")
DESC = os.path.join(ROOT, "config", "descartados.json")   # revisados que no valen (se miran otra vez al mes)
MAX_REVISAR = 150           # como mucho, juegos que se consultan a Steam por día
UA = {"User-Agent": "Mozilla/5.0 (OfertaGG-bot/1.0)"}
MAX = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 25
MIN_RESENAS = 1500          # juego ya lanzado: mínimo de reseñas en Steam
MIN_RESENAS_NUEVO = 150     # lanzado hace menos de 4 meses
TOP_PROXIMOS = 150          # reservas: solo si están en el top de ventas
ADULTO = {3, 4}             # Steam: contenido sexual -> fuera
LISTAS = ["topsellers", "globaltopsellers", "mostplayed", "popularnew"]


def log(*a):
    print(*a, flush=True)


def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            log("  reintento", i + 1, e)
            time.sleep(5 + i * 10)
    return None


def lista(nombre, paginas=4):
    ids = []
    for start in range(0, paginas * 100, 100):
        t = get(f"https://store.steampowered.com/search/results/?filter={nombre}&json=1&count=100&start={start}"
                f"&cc=es&category1=998&infinite=1")
        if not t:
            break
        try:
            got = re.findall(r'data-ds-appid="(\d+)"', json.loads(t).get("results_html", ""))
        except ValueError:
            break
        if not got:
            break
        ids += [int(x) for x in got]
        time.sleep(1)
    return list(dict.fromkeys(ids))


def fecha(s):
    for f in ("%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y"):
        try:
            return datetime.datetime.strptime(s, f).date()
        except (ValueError, TypeError):
            pass
    return None


def vale(appid, origen, rango):
    t = get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es&l=english")
    time.sleep(1.4)   # Steam limita a ~200 peticiones cada 5 minutos
    try:
        d = json.loads(t)[str(appid)]
    except Exception:
        return None
    if not d.get("success"):
        return None
    x = d["data"]
    if x.get("type") != "game" or x.get("is_free"):
        return None
    if ADULTO & set((x.get("content_descriptors") or {}).get("ids") or []):
        return None
    name = x.get("name") or ""
    if re.search(r"soundtrack|\bost\b|artbook|demo\b|playtest|benchmark|wallpaper", name, re.I):
        return None
    rec = (x.get("recommendations") or {}).get("total", 0)
    soon = x["release_date"]["coming_soon"]
    if soon:
        # próximo lanzamiento: solo si ya está entre los más vendidos (reservas de juegos grandes)
        return name if origen in ("topsellers", "globaltopsellers") and rango < TOP_PROXIMOS else None
    if not x.get("price_overview"):
        return None            # sin precio en España
    f = fecha(x["release_date"]["date"])
    nuevo = f and (datetime.date.today() - f).days < 120
    return name if rec >= MIN_RESENAS or (nuevo and rec >= MIN_RESENAS_NUEVO) else None


def main():
    cfg = json.load(open(CFG, encoding="utf-8"))
    tengo = set(cfg["juegos"])
    hoy = datetime.date.today()
    desc = json.load(open(DESC, encoding="utf-8")) if os.path.exists(DESC) else {}
    desc = {k: v for k, v in desc.items() if (hoy - datetime.date.fromisoformat(v)).days < 30}
    candidatos = []
    for nombre in LISTAS:
        ids = lista(nombre)
        log(f"{nombre}: {len(ids)}")
        for rango, a in enumerate(ids):
            if a not in tengo and str(a) not in desc and a not in {c[0] for c in candidatos}:
                candidatos.append((a, nombre, rango))
    log(f"{len(candidatos)} juegos que aún no están en la web; reviso hasta añadir {MAX}")
    nuevos = []
    for i, (a, origen, rango) in enumerate(candidatos):
        if len(nuevos) >= MAX or i >= max(MAX_REVISAR, MAX * 3):
            break
        n = vale(a, origen, rango)
        if n:
            nuevos.append(a)
            log(" +", a, n)
        else:
            desc[str(a)] = hoy.isoformat()
    json.dump(desc, open(DESC, "w", encoding="utf-8"), indent=0)
    if nuevos:
        cfg["juegos"] += nuevos
        json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log(f"Añadidos {len(nuevos)} juegos · total {len(cfg['juegos'])}")


if __name__ == "__main__":
    main()
