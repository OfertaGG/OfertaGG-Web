#!/usr/bin/env python3
"""
OfertaGG - robot de actualización.

Qué hace cada vez que se ejecuta:
  1. Lee la lista de juegos (config/juegos.json).
  2. Descarga de Steam los datos de cada juego (nombre, descripción, imágenes, precio oficial).
  3. Lee las ofertas de los afiliados (archivos feeds/*.json).
  4. Junta todo: los JUEGOS NUNCA SE BORRAN; solo se quitan las OFERTAS que han
     caducado o que la tienda ya no tiene. Si un juego no tiene ofertas, se queda
     con el precio normal de cada tienda.
  5. Marca como "Nueva oferta" las ofertas recién aparecidas en juegos populares,
     para que salgan arriba del todo en la web.
  6. Escribe site/data.json, que es lo que lee la web.

Modos:
  python scripts/update.py              -> actualización completa (lunes)
  python scripts/update.py --diario     -> solo ofertas: quita caducadas y mete
                                           las nuevas de juegos populares (cada día)
"""
import json, os, re, sys, glob, html, time, io, datetime, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
IMG = os.path.join(SITE, "img")
DATA = os.path.join(SITE, "data.json")
CACHE = os.path.join(ROOT, "config", "steam_cache.json")
NOW = datetime.datetime.now(datetime.timezone.utc)
TODAY = NOW.date()
DIARIO = "--diario" in sys.argv
NUEVA_DIAS = 7          # una oferta es "nueva" durante sus primeros 7 días
STORES = {"steam", "eneba", "instant", "kinguin", "loaded", "gamivo", "fanatical", "g2a"}
REGIONS = {"Global", "Europa", "Resto del mundo"}
PLATFORMS = {"pc", "xbox", "ps", "switch"}   # PC (Steam), Xbox, PlayStation, Nintendo Switch
GENRE_MAP = {"Rol": "RPG", "Simuladores": "Simulación", "Multijugador masivo": "Multijugador", "Free to Play": "Gratis"}
MESES = dict(ENE=1, FEB=2, MAR=3, ABR=4, MAY=5, JUN=6, JUL=7, AGO=8, SEP=9, OCT=10, NOV=11, DIC=12)
UA = {"User-Agent": "OfertaGG-bot/1.0"}


def log(*a):
    print(*a, flush=True)


def get_json(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            log("  reintento", i + 1, url, e)
            time.sleep(3 + i * 5)
    return None


def get_bytes(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read()
    except Exception:
        return None


def strip(s, n=None):
    s = re.sub(r"<br\s*/?>", "\n", s or "")
    s = re.sub(r"</(p|h\d|li|ul)>", "\n", s)
    s = re.sub(r"<li>", "• ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"\n\s*\n+", "\n\n", s).strip()
    if n and len(s) > n:
        s = s[:n].rsplit(" ", 1)[0] + "…"
    return s


def parse_date(s):
    m = re.match(r"(\d+) (\w+)\.? (\d{4})", s or "")
    if not m or m[2][:3].upper() not in MESES:
        return None
    return datetime.date(int(m[3]), MESES[m[2][:3].upper()], int(m[1])).isoformat()


# ---------- imágenes ----------
def save_img(url, path, width, q=72):
    if os.path.exists(path):
        return True
    b = get_bytes(url)
    if not b:
        return False
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(b)).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(path, "WEBP", quality=q, method=6)
        return True
    except Exception as e:
        log("  imagen falló", url, e)
        return False


def images(appid, d, featured):
    os.makedirs(IMG, exist_ok=True)
    base = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/"
    save_img((d.get("header_image") or base + "header.jpg"), f"{IMG}/{appid}_h.webp", 460)
    if featured:
        save_img(base + "library_hero.jpg", f"{IMG}/{appid}_hero.webp", 1600, 70)
    n = 0
    for s in (d.get("screenshots") or [])[:4]:
        if save_img(s["path_full"], f"{IMG}/{appid}_s{n}.webp", 1100, 70):
            n += 1
    return n, os.path.exists(f"{IMG}/{appid}_hero.webp")


def cover_images(appid, url):
    """Juegos sin Steam: con la portada de la tienda se hacen la cabecera y la imagen grande
    (portada centrada sobre un fondo difuminado de sí misma)."""
    h, s0 = f"{IMG}/{appid}_h.webp", f"{IMG}/{appid}_s0.webp"
    if os.path.exists(h) and os.path.exists(s0):
        return True
    b = get_bytes(url) if url else None
    if not b:
        return False
    try:
        from PIL import Image, ImageFilter
        im = Image.open(io.BytesIO(b)).convert("RGB")
        os.makedirs(IMG, exist_ok=True)
        for path, (w, hh) in ((h, (460, 215)), (s0, (1100, 515))):
            bg = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            top = max(0, (bg.height - hh) // 2)
            bg = bg.crop((0, top, w, top + hh)).filter(ImageFilter.GaussianBlur(18))
            fg = im.resize((round(im.width * hh / im.height), hh), Image.LANCZOS)
            if fg.width > w:
                fg = fg.resize((w, round(fg.height * w / fg.width)), Image.LANCZOS)
            bg.paste(fg, ((w - fg.width) // 2, (hh - fg.height) // 2))
            bg.save(path, "WEBP", quality=74, method=6)
        return True
    except Exception as e:
        log("  portada falló", url, e)
        return False


def build_manual(j, portadas):
    """Juego que no está en Steam (GTA VI, juegos de Nintendo...): los datos salen de config/juegos.json
    -> "sin_steam" y la portada de la tienda. No tiene precio oficial de Steam ni reseñas de Steam."""
    a = j["id"]
    sh = 1 if cover_images(a, portadas.get(str(a)) or j.get("img")) else 0
    rel = j.get("rel")
    return dict(id=a, n=j["n"], sd=j["sd"], ab=j.get("ab") or j["sd"], dev=j.get("dev", []), pub=j.get("pub", []),
                rel=rel, soon=bool(rel and rel > TODAY.isoformat()), g=j.get("g", []), mc=None, rec=0, rk=j.get("rk", 0),
                age=j.get("age", 0), ach=0, dlc=0, free=False, base=0, sh=sh, hero=False, feats=j.get("feats", []),
                langs=[], req="", reqr="", vid=0, ns=True)


# ---------- Steam ----------
def steam(appid, cache):
    d = get_json(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=es&l=spanish")
    time.sleep(1.2)  # Steam limita a ~200 peticiones cada 5 minutos
    if d and d.get(str(appid), {}).get("success"):
        cache[str(appid)] = d[str(appid)]["data"]
        return cache[str(appid)]
    log("  Steam no respondió, uso los datos guardados de", appid)
    return cache.get(str(appid))


def build_game(appid, d, cfg, old):
    po = d.get("price_overview") or {}
    free = bool(d.get("is_free"))
    base = round(po.get("initial", 0) / 100, 2)
    final = round(po.get("final", 0) / 100, 2)
    genres = [GENRE_MAP.get(g["description"], g["description"]) for g in d.get("genres", []) if g["description"] != "Acceso anticipado"]
    for tag, ids in cfg["etiquetas"].items():
        if appid in ids:
            genres.append(tag)
    genres = list(dict.fromkeys(genres))
    ab = max([strip(d.get("about_the_game"), 1600), strip(d.get("detailed_description"), 1600)], key=len)
    if len(ab) < 200:
        ab = strip(d.get("short_description", ""))
    req = d.get("pc_requirements") if isinstance(d.get("pc_requirements"), dict) else {}
    langs = strip(d.get("supported_languages", "")).split("\n")[0]
    langs = [l.strip(" *") for l in re.split(r",\s*", langs) if l.strip()][:14]
    feats = [c["description"] for c in d.get("categories", []) if c["description"] in (
        "Un jugador", "Multijugador", "Cooperativo", "Cooperativo en línea", "Multijugador en línea", "JcJ en línea", "Logros de Steam")]
    rec = (d.get("recommendations") or {}).get("total", 0) or (old or {}).get("rec", 0)
    featured = appid in cfg["destacados"]
    shots, hero = images(appid, d, featured)
    return dict(
        id=appid, n=d["name"].strip(), sd=strip(d.get("short_description", "")), ab=ab,
        dev=d.get("developers", []), pub=d.get("publishers", []),
        rel=parse_date(d["release_date"]["date"]), soon=d["release_date"]["coming_soon"],
        g=genres, mc=(d.get("metacritic") or {}).get("score"), rec=rec,
        age=int(d.get("required_age") or 0), ach=(d.get("achievements") or {}).get("total", 0),
        dlc=len(d.get("dlc", [])), free=free, base=base, sh=shots, hero=hero and featured,
        feats=feats, langs=langs,
        req=strip(req.get("minimum", ""), 900), reqr=strip(req.get("recommended", ""), 900),
        vid=len(d.get("movies", [])),
        steam=dict(p=final, was=base, off=po.get("discount_percent", 0)),
    )


# ---------- ofertas de afiliados ----------
def moved(r, rules):
    """config "mover": ofertas que las tiendas titulan igual pero son OTRO juego.
    Ej.: 'Resident Evil 4' para Xbox One o Switch es el original (2005), no el remake (que no salió ahí)."""
    for m in rules:
        if int(r["appid"]) != m["de"]:
            continue
        if "versiones" in m and (r.get("version") or "PC") not in m["versiones"]:
            continue
        if "ediciones" in m and (r.get("edition") or "Standard") not in m["ediciones"]:
            continue
        return m.get("a")          # None = esa oferta no es de ningún juego de la lista: fuera
    return int(r["appid"])


def read_feeds(cfg=None):
    """Cada tienda deja un archivo feeds/<tienda>.json con una lista de ofertas:
    {"appid":1091500,"store":"eneba","platform":"pc","version":"PC","edition":"Standard","region":"Global",
     "price":35.25,"was":59.99,"ends":"2026-10-20","url":"https://...enlace de afiliado..."}
    "ends" vacío o null = precio normal (no es oferta)."""
    rules = (cfg or {}).get("mover") or []
    offers = []
    for f in sorted(glob.glob(os.path.join(ROOT, "feeds", "*.json"))):
        try:
            rows = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            log("  feed roto, lo salto:", f, e)
            continue
        for r in rows:
            if r.get("store") not in STORES or r.get("region") not in REGIONS:
                continue
            try:
                pf = r.get("platform") or "pc"
                if pf not in PLATFORMS:
                    continue
                appid = moved(r, rules)
                if appid is None:
                    continue
                offers.append(dict(appid=appid, s=r["store"], pf=pf, pv=r.get("version") or "PC",
                                   ed=r.get("edition") or "Standard",
                                   rg=r["region"], p=round(float(r["price"]), 2), was=round(float(r.get("was") or r["price"]), 2),
                                   exp=r.get("ends") or None, url=r.get("url") or None, since=r.get("since") or None))
            except Exception:
                continue
    return offers


def alive(o):
    return not o.get("exp") or o["exp"] >= TODAY.isoformat()


def key(o):
    return (o["s"], o.get("pf", "pc"), o.get("pv", "PC"), o["ed"], o["rg"], o.get("exp") or "")


def main():
    cfg = json.load(open(os.path.join(ROOT, "config", "juegos.json"), encoding="utf-8"))
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    old = json.load(open(DATA, encoding="utf-8")) if os.path.exists(DATA) else {"games": []}
    old_games = {g["id"]: g for g in old["games"]}
    popular = lambda g: g.get("rec", 0) >= cfg["umbral_popular"] or g["id"] in cfg["populares_extra"] or g.get("ns")
    sin_steam = {j["id"]: j for j in cfg.get("sin_steam", [])}
    pp = os.path.join(ROOT, "config", "portadas.json")
    portadas = json.load(open(pp, encoding="utf-8")) if os.path.exists(pp) else {}

    feeds = read_feeds(cfg)
    log(f"Modo: {'diario' if DIARIO else 'completo'} · {len(cfg['juegos'])} juegos · {len(feeds)} ofertas en los feeds")

    games, stats = [], dict(nuevas=0, quitadas=0, cambiadas=0)
    for appid in cfg["juegos"] + list(sin_steam):
        prev = old_games.get(appid)
        if DIARIO and prev and not popular(prev):
            g = dict(prev)                       # juego no popular: en modo diario no se pide nada a Steam,
            prev_by_key = {key(o): o for o in prev["o"]}   # pero sí se refrescan los precios de los afiliados
            fresh = [dict(o) for o in feeds if o["appid"] == appid and alive(o)]
            for o in fresh:
                o.pop("appid", None)
                p = prev_by_key.get(key(o))
                o["since"] = o.get("since") or (p.get("since") if p else TODAY.isoformat())
            g["o"] = [o for o in prev["o"] if o.get("official") and alive(o)] + fresh
            stats["quitadas"] += len(set(prev_by_key) - {key(o) for o in g["o"]})
            games.append(g)
            continue
        if appid in sin_steam:
            g = build_manual(sin_steam[appid], portadas)
            if not g["sh"]:
                log("  sin portada todavía, no lo enseño:", g["n"])
                continue
        else:
            d = steam(appid, cache)
            if not d:
                if prev:
                    games.append(prev)
                continue
            g = build_game(appid, d, cfg, prev)
        log(" ·", g["n"])

        # 1) precio oficial de Steam, siempre presente (si el juego está en Steam)
        offers = []
        if not g["free"] and "steam" in g:
            st = g["steam"]
            offers.append(dict(s="steam", pf="pc", pv="PC", ed="Standard", rg="Global", p=st["p"] if not g["soon"] else st["was"],
                               was=st["was"], exp=None, official=True, url=None))
        # 2) ofertas de los afiliados para este juego (vivas)
        tope = sin_steam[appid].get("max", 100) * 1.4 if appid in sin_steam else None   # precios absurdos fuera
        offers += [dict(o) for o in feeds if o["appid"] == appid and alive(o) and not (tope and o["p"] > tope)]
        for o in offers:
            o.pop("appid", None)

        # 3) comparar con la semana anterior: fecha en que apareció cada oferta
        prev_by_key = {key(o): o for o in (prev or {}).get("o", [])}
        for o in offers:
            p = prev_by_key.get(key(o))
            if o.get("since"):                   # el feed ya dice desde cuándo existe la oferta
                pass
            elif p:
                o["since"] = p.get("since", TODAY.isoformat())
            if p:
                if abs(p["p"] - o["p"]) > 0.009:
                    stats["cambiadas"] += 1
            if not p:
                o["since"] = o.get("since") or (TODAY.isoformat() if prev else "2000-01-01")
                if prev and o.get("exp"):
                    stats["nuevas"] += 1
        stats["quitadas"] += len(set(prev_by_key) - {key(o) for o in offers})
        g["o"] = offers

        # 4) "nueva oferta" en juego popular -> destacado arriba del todo
        g["pop"] = popular(g)
        g.pop("steam", None)
        games.append(g)

    games.sort(key=lambda g: -g.get("rec", 0))
    out = dict(updated=NOW.isoformat(timespec="minutes"), mode="diario" if DIARIO else "completo",
               nueva_dias=NUEVA_DIAS, demo=any(os.path.basename(f).startswith("demo") for f in glob.glob(os.path.join(ROOT, "feeds", "*.json"))),
               games=games)
    json.dump(out, open(DATA, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    log(f"Listo: {len(games)} juegos · {stats['nuevas']} ofertas nuevas · {stats['cambiadas']} precios cambiados · {stats['quitadas']} ofertas quitadas")


if __name__ == "__main__":
    main()
