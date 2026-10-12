#!/usr/bin/env python3
"""
SOLO PARA LA DEMO. Crea feeds/demo.json con precios de ejemplo de las tiendas
mientras no tengamos los feeds reales de los afiliados.
Cuando lleguen los feeds reales: borra feeds/demo.json y este script deja de usarse.

  python scripts/demo_feeds.py                 -> ofertas de ejemplo normales
  python scripts/demo_feeds.py --novedades     -> además, ofertas recién salidas en juegos populares
"""
import json, os, random, datetime, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cache = json.load(open(os.path.join(ROOT, "config", "steam_cache.json"), encoding="utf-8"))
TODAY = datetime.date.today()
STORES = ["eneba", "instant", "kinguin", "loaded", "gamivo", "fanatical"]
NO_DEALS = {292030, 632470, 413150, 2878980}       # juegos sin ofertas esta semana (para ver "precio base")
HOT = {3764200: ("eneba", .62), 2947440: ("instant", .58), 2124490: ("loaded", .27)}  # novedades

rows = []
for k, d in cache.items():
    appid = int(k)
    if d.get("is_free"):
        continue
    r = random.Random(appid)
    po = d.get("price_overview") or {}
    base = round(po.get("initial", 0) / 100, 2)
    if not base:
        continue
    soon = d["release_date"]["coming_soon"]
    eds = ["Standard"] + (["Deluxe"] if len(d.get("dlc", [])) >= 2 else [])
    for ed in eds:
        eb = base if ed == "Standard" else round(base * 1.35, 2)
        for s in r.sample(STORES, r.randint(3, 6)):
            regs = (["Global", "Europa"] if r.random() < .5 else [r.choice(["Global", "Europa"])]) + (["Resto del mundo"] if r.random() < .25 else [])
            for rg in regs:
                f = r.uniform(.80, .95) if soon else r.uniform(.5, .8)
                if rg == "Resto del mundo": f *= .8
                if rg == "Europa": f *= 1.02
                deal = r.random() < .65 and appid not in NO_DEALS
                p = round(eb * f, 2) if deal else round(eb * min(f + .12, .99), 2)
                ends = (TODAY + datetime.timedelta(days=r.randint(1, 9))).isoformat() if deal else None
                rows.append(dict(appid=appid, store=s, edition=ed, region=rg, price=p, was=eb, ends=ends, url=None, since="2000-01-01"))
                if r.random() < .18 and deal:   # oferta ya caducada: el robot la tiene que quitar
                    rows.append(dict(appid=appid, store=s, edition=ed, region=rg, price=round(p * .85, 2), was=eb,
                                     ends=(TODAY - datetime.timedelta(days=r.randint(1, 6))).isoformat(), url=None))

if "--novedades" in sys.argv:
    rows = [x for x in rows if not (x["appid"] in HOT and x["store"] == HOT[x["appid"]][0] and x["edition"] == "Standard")]
    for appid, (s, off) in HOT.items():
        d = cache.get(str(appid))
        if not d: continue
        base = round((d.get("price_overview") or {}).get("initial", 0) / 100, 2)
        for rg in ("Global", "Europa"):
            rows.append(dict(appid=appid, store=s, edition="Standard", region=rg, price=round(base * (1 - off) * (1.02 if rg == "Europa" else 1), 2),
                             was=base, ends=(TODAY + datetime.timedelta(days=6)).isoformat(), url=None, since=TODAY.isoformat()))

os.makedirs(os.path.join(ROOT, "feeds"), exist_ok=True)
json.dump(rows, open(os.path.join(ROOT, "feeds", "demo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(rows), "ofertas de ejemplo")
