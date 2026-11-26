"""
Feed de Kinguin -> feeds/kinguin.json

Kinguin publica un XML enorme (~2 GB) con todo su catálogo. Este script lo lee
"en streaming" (sin guardarlo en disco), se queda solo con los juegos de
config/juegos.json y guarda la oferta más barata de cada plataforma, versión,
edición y región, con tu enlace de afiliado.

Plataformas: PC (claves de Steam), Xbox, PlayStation y Nintendo Switch.
Solo CLAVES / CÓDIGOS para canjear en tu cuenta: nada de cuentas, gifts,
DLC sueltos, monedas ni tarjetas.

Variables (secrets de GitHub):
  KINGUIN_FEED_URL  enlace del feed que te mandó Kinguin
  KINGUIN_REF       tu ID de referido (se añade a cada enlace como &ref=ID)
"""
import json, os, re, sys, time, difflib, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "feeds", "kinguin.json")
NAMES_EN = os.path.join(ROOT, "config", "nombres_en.json")
FEED = os.environ.get("KINGUIN_FEED_URL") or "https://feeds.kinguin.net/xml/AFF_multicurrency_en_AED.xml"
REF = (os.environ.get("KINGUIN_REF") or "").strip()
G = "{http://base.google.com/ns/1.0}"
UA = {"User-Agent": "OfertaGG-bot/1.0"}

# plataforma de Kinguin -> (plataforma en la web, versión que se enseña)
PLATFORMS = {
    "Steam": ("pc", "PC"),
    "Xbox One": ("xbox", "Xbox One / Series X|S"),
    "Xbox Series X|S": ("xbox", "Xbox Series X|S"),
    "PlayStation 4": ("ps", "PS4"),
    "PlayStation 5": ("ps", "PS5"),
    "PlayStation": ("ps", "PlayStation"),
    "Nintendo Switch": ("switch", "Switch"),
    "Nintendo": ("switch", "Switch"),
    "Nintendo Switch 2": ("switch", "Switch 2"),
}
MAX_VS_STEAM = {"pc": 1.3, "xbox": 1.6, "ps": 1.6, "switch": 1.6}   # precios absurdos fuera

EDITION = re.compile(r"\b((?:digital |super |special |next level |vault |revolution )?(?:deluxe|ultimate|gold|premium|complete|definitive|"
                     r"collector'?s|commander|all-star|legendary|standard|game of the year|goty|director'?s cut|enhanced|cross-gen|next level|vault|revolution|champions?|anniversary|year \d)"
                     r"(?: edition| bundle)?)$", re.I)
# Códigos de región que Kinguin mete en el título
REGION_TOKENS = (r"(?:EU/NA|EU|EMEA|NA|US|UK|CA|AU|NZ|DE|FR|IT|ES|PL|UA|TR|CN|JP|IN|KR|HK|BR|MX|AR|CO|CL|PE|ZA|SA|AE|"
                 r"ASIA(?:/Oceania)?|SEA(?:/Oceania)?|LATAM(?:/RU/CIS)?|Latin America|South America|North America|"
                 r"European Union|RU/CIS|TR/RU/CIS/LATAM|CIS|RoW|ROW|MEA|Global|WW)")
CUT_PLATFORM = re.compile(r"\s(?:PC\s+)?(?:Steam|XBOX|Xbox|PS4|PS5|PSN|PlayStation|Nintendo|Switch|Windows 10)\b.*$")
BAD_WORDS = re.compile(r"Account|Access|Gift|Altergift|VPN|Bundle|Pack\b|\bDLC\b(?!.*Pre-Order)|Season Pass|Upgrade|Currency|Points|"
                       r"Coins|Credits|Subscription|Membership|Mystery|Random", re.I)


def log(*a):
    print(*a, flush=True)


def norm(s):
    """Nombre simplificado para comparar. OJO: el año se queda ("Resident Evil 4 (2005)" no es el remake de 2023)."""
    s = s.lower().replace("’", "'")
    s = re.sub(r"[™®©]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


YEAR_ONLY = re.compile(r"\s*(19[6-9]\d|20[0-4]\d)\s*")
VARIANT = re.compile(r"\b(remake|remaster(?:ed)?|classic|original|hd|legacy|reloaded)\b", re.I)


def clean_parens(s):
    """Quita lo que va entre paréntesis SALVO lo que dice qué juego es:
    'Resident Evil 2 (1998)' -> 'Resident Evil 2 1998'; '... (Ultimate HD Edition)' se queda;
    '(PC)', '(EU)', '(Valid until June 2027)' se van."""
    def keep(m):
        t = m.group(1)
        if YEAR_ONLY.fullmatch(t) or (VARIANT.search(t) and len(t) <= 30):
            return " " + t.strip() + " "
        return " "
    return re.sub(r"\s*\((.*?)\)\s*", keep, s).strip()


def no_years(s):
    return " ".join(re.sub(r"\b(19[6-9]\d|20[0-4]\d)\b", " ", s).split())


def build_aliases(ids, names_en, cfg):
    """Nombres con los que reconocer cada juego en las tiendas:
       - su nombre de Steam en inglés
       - nombre + año de salida ("Resident Evil 4 2023", así lo titulan muchas tiendas)
       - nombre + "Remake" si no hay otro juego de la lista con el mismo nombre
       - los alias escritos a mano en config/juegos.json -> "alias"
    """
    years = {}
    data = os.path.join(ROOT, "site", "data.json")
    if os.path.exists(data):
        for g in json.load(open(data, encoding="utf-8"))["games"]:
            if g.get("rel"):
                years[g["id"]] = g["rel"][:4]
    al = {a: set() for a in ids}
    bases = {}
    for a in ids:
        if a in names_en:
            n = norm(names_en[a])
            al[a].add(n)
            bases.setdefault(no_years(n), []).append(a)
            y = years.get(a)
            if y and y not in n.split():
                al[a].add(f"{n} {y}")
    for b, lst in bases.items():
        if len(lst) == 1 and b and "remake" not in b.split():
            al[lst[0]].add(b + " remake")
    for a, extra in (cfg.get("alias") or {}).items():
        if int(a) in al:
            al[int(a)].update(norm(x) for x in extra)
    for j in cfg.get("sin_steam", []):          # juegos sin Steam: su nombre y los que pongas en "buscar"
        al[j["id"]] = {norm(x) for x in [j["n"]] + j.get("buscar", [])}
    return al


def english_names(ids):
    """Nombre en inglés de cada juego (Kinguin titula en inglés). Se guarda en caché en el repo."""
    cache = json.load(open(NAMES_EN, encoding="utf-8")) if os.path.exists(NAMES_EN) else {}
    for i in ids:
        if str(i) in cache:
            continue
        try:
            url = f"https://store.steampowered.com/api/appdetails?appids={i}&l=english&filters=basic"
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                d = json.load(r)[str(i)]
            if d.get("success"):
                cache[str(i)] = d["data"]["name"]
        except Exception as e:
            log("  sin nombre en inglés", i, e)
        time.sleep(1.3)   # Steam limita a ~200 peticiones cada 5 minutos
    json.dump(cache, open(NAMES_EN, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return {int(k): v for k, v in cache.items()}


def region_of(title, rg):
    """Global / Europa / Resto del mundo. Ante la duda, 'Resto del mundo' (no se recomienda en España)."""
    t = " " + re.sub(r"\(.*?\)", " ", title) + " "
    if re.search(r" (EU|EU/NA|EMEA|European Union) ", t):
        return "Europa"
    if re.search(r" " + REGION_TOKENS + r" ", t):
        return "Global" if re.search(r" (Global|WW) ", t) else "Resto del mundo"
    rg = (rg or "").upper()
    if "REGION FREE" in rg or rg.endswith("GLOBAL"):
        return "Global"
    if rg.endswith("EUROPE") or "EUROPE - ALL" in rg:
        return "Europa"
    return "Resto del mundo"


def split_title(title):
    """'Resident Evil Village Gold Edition EU XBOX One CD Key' -> ('Resident Evil Village', 'Gold Edition')"""
    core = clean_parens(title)
    core = CUT_PLATFORM.sub("", core)
    core = re.sub(r"\s+PRE-ORDER\b", "", core, flags=re.I)
    core = re.sub(r"\s+\+\s*Pre-Order Bonus.*$", "", core, flags=re.I)
    core = re.sub(r"\s+v\d+\b", "", core)
    for _ in range(2):
        core = re.sub(r"\s+" + REGION_TOKENS + r"$", "", core).strip()
    edition = "Standard"
    m = EDITION.search(core)
    if m:
        edition = m.group(1).strip().title().replace("'S", "'s").replace("Goty", "GOTY")
        core = core[:m.start()].strip(" :-–")
        if edition.lower() in ("standard", "standard edition"):
            edition = "Standard"
    return core, edition


ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xv", "xvi"}


VARIANT_WORDS = {"remake": "remake", "remaster": "remastered", "remastered": "remastered", "classic": "classic",
                 "original": "original", "hd": "hd", "legacy": "legacy", "reloaded": "reloaded"}


def nums(s):
    """Lo que distingue juegos de la misma saga: números (2, 3, IV...), años (1998, 2023)
    y palabras como Remake / Remastered / HD. Así Resident Evil 2 (1998) no se mezcla con el de 2019."""
    return {VARIANT_WORDS.get(t, t) for t in s.split() if t.isdigit() or t in ROMAN or t in VARIANT_WORDS}


def close(c, n):
    return c == n or (nums(c) == nums(n) and difflib.SequenceMatcher(None, c, n).ratio() >= 0.92)


def same_game(core, names):
    """Para claves de PC que ya traen el número de Steam: solo comprueba que no sea un DLC
    o algo con otro nombre. El año se ignora ('Resident Evil 4 (2023)' = 'Resident Evil 4')."""
    c = norm(core)
    return any(close(c, n) or close(no_years(c), no_years(n)) for n in names)


def read_item(el):
    """Datos básicos de un producto, o None si no es una clave de juego para PC/consola."""
    plat = (el.findtext(G + "platform") or "").strip()
    if plat not in PLATFORMS:
        return None
    if (el.findtext(G + "product_type") or "") not in ("GAME", "PREORDER"):
        return None
    title = (el.findtext("title") or "").strip()
    if "Key" not in title or BAD_WORDS.search(title):
        return None
    if (el.findtext(G + "availability") or "") != "in stock":
        return None
    eur = next((pd for pd in el.iter("price_details") if pd.findtext("currency") == "EUR"), None)
    if eur is None:
        return None
    try:
        price = round(float(eur.findtext("price")), 2)
    except (TypeError, ValueError):
        return None
    link = (eur.findtext("link") or "").strip()
    if not link or price <= 0:
        return None
    pf, pv = PLATFORMS[plat]
    sid = el.findtext(G + "steam_id") or ""
    core, edition = split_title(title)
    return dict(title=title, pf=pf, pv=pv, sid=int(sid) if sid.isdigit() else None, core=core, edition=edition,
                region=region_of(title, el.findtext(G + "region")), price=price, link=link,
                img=(el.findtext(G + "image_link") or "").strip())


def main():
    cfg = json.load(open(os.path.join(ROOT, "config", "juegos.json"), encoding="utf-8"))
    sin_steam = {j["id"]: j for j in cfg.get("sin_steam", [])}    # juegos que no están en Steam (GTA VI, Nintendo...)
    ids = cfg["juegos"] + list(sin_steam)
    idset = set(ids)
    names_en = english_names(cfg["juegos"])
    steam_base = {a: j.get("max", 100) / MAX_VS_STEAM["ps"] for a, j in sin_steam.items()}
    data = os.path.join(ROOT, "site", "data.json")
    if os.path.exists(data):
        for g in json.load(open(data, encoding="utf-8"))["games"]:
            if g.get("base"):
                steam_base[g["id"]] = g["base"]
    if not REF:
        log("AVISO: falta KINGUIN_REF -> los enlaces no llevan tu ID de afiliado")

    src = sys.argv[1] if len(sys.argv) > 1 else None   # para probar con un archivo local
    stream = open(src, "rb") if src else urllib.request.urlopen(urllib.request.Request(FEED, headers=UA), timeout=120)
    pc_items, console_items, n = [], [], 0
    for _, el in ET.iterparse(stream, events=("end",)):
        if el.tag != "item":
            continue
        n += 1
        it = read_item(el)
        el.clear()
        if not it:
            continue
        if it["pf"] == "pc":
            if it["sid"] in idset and "CD Key" in it["title"]:
                pc_items.append(it)
        else:
            console_items.append(it)
    if n < 1000:
        log(f"El feed parece incompleto ({n} productos). No toco feeds/kinguin.json")
        sys.exit(0)

    # nombres con los que reconocer cada juego: el de Steam en inglés + el que usa Kinguin en sus claves de Steam
    aliases = build_aliases(ids, names_en, cfg)
    for it in pc_items:   # sin nombre de Steam: uso el de Kinguin
        if it["edition"] == "Standard" and it["sid"] not in names_en:
            aliases[it["sid"]].add(norm(it["core"]))
    by_name = {}
    for a, al in aliases.items():
        for nm in al:
            if nm:
                by_name.setdefault(nm, a)

    offers = []
    for it in pc_items:
        if same_game(it["core"], aliases[it["sid"]]):
            offers.append((it["sid"], it))
    for it in console_items:
        a = it["sid"] if it["sid"] in idset else by_name.get(norm(it["core"]))
        if a is None:
            c = norm(it["core"])
            hit = [h for h in difflib.get_close_matches(c, by_name.keys(), n=3, cutoff=0.92) if close(c, h)]
            a = by_name[hit[0]] if hit else None
        if a is not None:
            offers.append((a, it))

    best, imgs = {}, {}
    for a, it in offers:
        if a in sin_steam and it["edition"] == "Standard" and it["img"] and it["region"] in ("Europa", "Global"):
            imgs.setdefault(a, it["img"])      # portada para los juegos que no tienen ficha de Steam
        base = steam_base.get(a)
        if base and it["edition"] == "Standard" and it["price"] > base * MAX_VS_STEAM[it["pf"]]:
            continue
        k = (a, it["pf"], it["pv"], it["edition"], it["region"])
        if k not in best or it["price"] < best[k]["price"]:
            link = it["link"]
            url = link + ("&" if "?" in link else "?") + "ref=" + REF if REF else link
            best[k] = dict(appid=a, store="kinguin", platform=it["pf"], version=it["pv"], edition=it["edition"],
                           region=it["region"], price=it["price"], was=it["price"], ends="", url=url)
    rows = sorted(best.values(), key=lambda o: (o["appid"], o["platform"], o["version"], o["edition"], o["region"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({str(k): v for k, v in imgs.items()}, open(os.path.join(ROOT, "config", "portadas.json"), "w", encoding="utf-8"), indent=0)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    per = {}
    for o in rows:
        per[o["platform"]] = per.get(o["platform"], 0) + 1
    log(f"Kinguin: {n} productos leídos · {len(rows)} ofertas para {len({o['appid'] for o in rows})} juegos · por plataforma: {per}")


if __name__ == "__main__":
    main()
