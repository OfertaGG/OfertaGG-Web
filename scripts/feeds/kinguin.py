"""
Feed de Kinguin -> feeds/kinguin.json

Kinguin publica un XML enorme (~2 GB) con todo su catálogo. Este script lo lee
"en streaming" (sin guardarlo en disco), se queda solo con los juegos de
config/juegos.json (por su número de Steam) y guarda la oferta más barata de cada
edición y región, con tu enlace de afiliado.

Variables (secrets de GitHub):
  KINGUIN_FEED_URL  enlace del feed que te mandó Kinguin
  KINGUIN_REF       tu ID de referido (se añade a cada enlace como &r=ID)

Solo claves de Steam (nada de cuentas, gifts ni Xbox). Precios en euros.
"""
import json, os, re, sys, difflib, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "feeds", "kinguin.json")
NAMES_EN = os.path.join(ROOT, "config", "nombres_en.json")
FEED = os.environ.get("KINGUIN_FEED_URL") or "https://feeds.kinguin.net/xml/AFF_multicurrency_en_AED.xml"
REF = (os.environ.get("KINGUIN_REF") or "").strip()
G = "{http://base.google.com/ns/1.0}"
UA = {"User-Agent": "OfertaGG-bot/1.0"}

EDITION = re.compile(r"\b((?:digital |super |special )?(?:deluxe|ultimate|gold|premium|complete|definitive|collector'?s|commander|"
                     r"all-star|legendary|standard|game of the year|goty|director'?s cut|enhanced|year \d)(?: edition)?)$", re.I)
# Códigos de región que Kinguin mete en el título
REGION_TOKENS = r"(?:EU/NA|EU|EMEA|NA|US|UK|CA|AU|DE|FR|IT|ES|PL|UA|TR|CN|JP|IN|ASIA(?:/Oceania)?|SEA(?:/Oceania)?|LATAM(?:/RU/CIS)?|Latin America|RU/CIS|TR/RU/CIS/LATAM|CIS|RoW|MEA|Global|ROW)"


def log(*a):
    print(*a, flush=True)


def norm(s):
    s = s.lower().replace("’", "'")
    s = re.sub(r"[™®©]", "", s)
    s = re.sub(r"\(\d{4}\)", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def english_names(ids):
    """Nombre en inglés de cada juego (Kinguin titula en inglés). Se guarda en caché."""
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
    json.dump(cache, open(NAMES_EN, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return {int(k): v for k, v in cache.items()}


def region_of(title, rg):
    """Global / Europa / Resto del mundo. Ante la duda, 'Resto del mundo' (no se recomienda en España)."""
    t = " " + title + " "
    if re.search(r" (EU|EU/NA|EMEA) ", t):
        return "Europa"
    if re.search(r" " + REGION_TOKENS + r" ", t):
        return "Resto del mundo"          # UK, UA, NA, LATAM, ASIA… no garantizadas en España
    rg = (rg or "").upper()
    if "REGION FREE" in rg:
        return "Global"
    if rg.endswith("EUROPE") or "EUROPE - ALL" in rg:
        return "Europa"
    return "Resto del mundo"


def parse_item(el, names, steam_base):
    title = (el.findtext("title") or "").strip()
    sid = el.findtext(G + "steam_id") or ""
    if not sid.isdigit() or int(sid) not in names:
        return None
    appid = int(sid)
    if (el.findtext(G + "platform") or "").strip() != "Steam":
        return None
    if (el.findtext(G + "product_type") or "") not in ("GAME", "PREORDER"):
        return None
    if "CD Key" not in title or re.search(r"Account|Gift|VPN|Bundle|Xbox|\bDLC\b(?!.*Pre-Order)", title, re.I):
        return None
    if (el.findtext(G + "availability") or "") != "in stock":
        return None
    eur = None
    for pd in el.iter("price_details"):
        if pd.findtext("currency") == "EUR":
            eur = pd
            break
    if eur is None:
        return None
    try:
        price = round(float(eur.findtext("price")), 2)
    except (TypeError, ValueError):
        return None
    link = (eur.findtext("link") or "").strip()
    if not link or price <= 0:
        return None

    # título -> nombre del juego + edición
    core = re.sub(r"\s*\(.*?\)\s*", " ", title)
    core = re.sub(r"\s+(PC\s+)?Steam CD Key.*$", "", core)
    core = re.sub(r"\s+PRE-ORDER\b", "", core, flags=re.I)
    core = re.sub(r"\s+v\d+\b", "", core)
    core = re.sub(r"\s+\+\s*Pre-Order Bonus.*$", "", core, flags=re.I)
    core = re.sub(r"\s+" + REGION_TOKENS + r"$", "", core).strip()
    edition = "Standard"
    m = EDITION.search(core)
    name = names[appid]
    if m and norm(core) != norm(name):
        edition = m.group(1).strip().title().replace("'S", "'s")
        core = core[:m.start()].strip(" :-")
        if edition.lower() in ("standard", "standard edition"):
            edition = "Standard"
    # el resto del título tiene que ser el mismo juego (evita mezclar secuelas, packs, etc.)
    if norm(core) != norm(name) and difflib.SequenceMatcher(None, norm(core), norm(name)).ratio() < 0.9:
        return None
    # precios absurdos (vendedores con precio inflado): fuera
    base = steam_base.get(appid)
    if base and edition == "Standard" and price > base * 1.3:
        return None

    url = link + ("&" if "?" in link else "?") + "r=" + REF if REF else link
    return dict(appid=appid, store="kinguin", edition=edition, region=region_of(title, el.findtext(G + "region")),
                price=price, was=price, ends="", url=url)


def main():
    cfg = json.load(open(os.path.join(ROOT, "config", "juegos.json"), encoding="utf-8"))
    ids = cfg["juegos"]
    names = english_names(ids)
    data = os.path.join(ROOT, "site", "data.json")
    steam_base = {}
    if os.path.exists(data):
        for g in json.load(open(data, encoding="utf-8"))["games"]:
            if g.get("base"):
                steam_base[g["id"]] = g["base"]
    if not REF:
        log("AVISO: falta KINGUIN_REF -> los enlaces no llevan tu ID de afiliado")

    src = sys.argv[1] if len(sys.argv) > 1 else None   # para probar con un archivo local
    stream = open(src, "rb") if src else urllib.request.urlopen(urllib.request.Request(FEED, headers=UA), timeout=120)
    best, n = {}, 0
    for _, el in ET.iterparse(stream, events=("end",)):
        if el.tag != "item":
            continue
        n += 1
        o = parse_item(el, names, steam_base)
        el.clear()
        if o:
            k = (o["appid"], o["edition"], o["region"])
            if k not in best or o["price"] < best[k]["price"]:
                best[k] = o
    rows = sorted(best.values(), key=lambda o: (o["appid"], o["edition"], o["region"]))
    if n < 1000:
        log(f"El feed parece incompleto ({n} productos). No toco feeds/kinguin.json")
        sys.exit(0)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    log(f"Kinguin: {n} productos leídos · {len(rows)} ofertas para {len({o['appid'] for o in rows})} juegos")


if __name__ == "__main__":
    main()
