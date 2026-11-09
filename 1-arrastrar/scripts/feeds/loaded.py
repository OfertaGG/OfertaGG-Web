"""
Catálogo de Loaded (vía Impact) -> feeds/loaded.json

Descarga el catálogo en euros de Loaded con la API de Impact (los enlaces ya
llevan tu ID de afiliado), se queda con los juegos de config/juegos.json y
guarda la oferta más barata de cada plataforma, edición y región.

Solo claves de PC (Steam), Xbox, PlayStation y Switch. Nada de DLC, packs,
monedas ni tarjetas.

Variables (secrets de GitHub):
  IMPACT_SID     Account SID de tu cuenta de Impact
  IMPACT_TOKEN   Auth Token de tu cuenta de Impact
  LOADED_CATALOG (opcional) id del catálogo; por defecto 12138 = Loaded-ProductFeed_EUR_English

Para probar con un archivo exportado desde Impact (TSV):
  python scripts/feeds/loaded.py archivo.txt
"""
import base64, csv, json, os, re, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kinguin import ROOT, EDITION, norm, close, english_names, log   # mismas reglas que Kinguin

OUT = os.path.join(ROOT, "feeds", "loaded.json")
SID = (os.environ.get("IMPACT_SID") or "").strip()
TOKEN = (os.environ.get("IMPACT_TOKEN") or "").strip()
CATALOG = (os.environ.get("LOADED_CATALOG") or "12138").strip()
MAX_VS_STEAM = {"pc": 1.3, "xbox": 1.6, "ps": 1.6, "switch": 1.6}

BAD = re.compile(r"\bDLC\b|Soundtrack|Season Pass|Expansion|Upgrade|Pack\b|Bundle|Currency|Points|Coins|Credits|"
                 r"Gift Card|Wallet|Subscription|Membership|Artbook|Costume|Skin\b|Pre-?Purchase Bonus", re.I)
SUFFIX = re.compile(r"\s+(PC|Mac|Steam|Xbox.*|PS4.*|PS5.*|PlayStation.*|Switch.*|Nintendo.*)$", re.I)


def platform_of(p):
    p = (p or "").lower()
    if p == "steam":
        return "pc", "PC"
    if "xbox" in p:
        if "one" in p and "series" in p:
            return "xbox", "Xbox One / Series X|S"
        if "series" in p:
            return "xbox", "Xbox Series X|S"
        if "play anywhere" in p:
            return "xbox", "Xbox Play Anywhere"
        return "xbox", "Xbox One"
    if "playstation 5" in p or "ps5" in p:
        return "ps", "PS5"
    if "playstation" in p or "ps4" in p or "psn" in p:
        return "ps", "PS4" if "4" in p else "PlayStation"
    if "switch 2" in p:
        return "switch", "Switch 2"
    if "switch" in p or "nintendo" in p:
        return "switch", "Switch"
    return None, None


def region_of(r):
    r = (r or "").lower()
    if r in ("worldwide", "global", "region free"):
        return "Global"
    if r.startswith("europe"):
        return "Europa"
    return "Resto del mundo"


def split_name(name):
    core = re.sub(r"\s*\(.*?\)\s*", " ", name).strip()
    core = SUFFIX.sub("", core).strip(" -–:")
    edition = "Standard"
    m = EDITION.search(core)
    if m:
        edition = m.group(1).strip().title().replace("'S", "'s").replace("Goty", "GOTY")
        core = core[:m.start()].strip(" :-–")
        if edition.lower() in ("standard", "standard edition"):
            edition = "Standard"
    return core, edition


def get(d, *keys):
    """Lee un campo aunque cambie la forma del nombre (API: CurrentPrice / TSV: Current Price)."""
    low = {k.replace(" ", "").lower(): v for k, v in d.items()}
    for k in keys:
        v = low.get(k.replace(" ", "").lower())
        if v not in (None, ""):
            return v
    return ""


def items_from_api():
    if not (SID and TOKEN):
        log("AVISO: faltan IMPACT_SID / IMPACT_TOKEN -> no actualizo Loaded")
        sys.exit(0)
    auth = base64.b64encode(f"{SID}:{TOKEN}".encode()).decode()
    url = f"https://api.impact.com/Mediapartners/{SID}/Catalogs/{CATALOG}/Items?PageSize=1000"
    page = 0
    while url:
        page += 1
        req = urllib.request.Request(url, headers={"Authorization": "Basic " + auth, "Accept": "application/json",
                                                   "User-Agent": "OfertaGG-bot/1.0"})
        for i in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = json.load(r)
                break
            except Exception as e:
                log("  reintento Impact", i + 1, e)
                time.sleep(5 + i * 10)
        else:
            log("Impact no responde; no toco feeds/loaded.json")
            sys.exit(0)
        for it in data.get("Items", []):
            yield it
        nxt = data.get("@nextpageuri") or data.get("NextPageUri") or ""
        url = ("https://api.impact.com" + nxt) if nxt.startswith("/") else (nxt or None)
        if page > 500:
            break
        time.sleep(0.4)


def items_from_file(path):
    csv.field_size_limit(10 ** 9)
    for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"):
        if r.get("Catalog Id") in (CATALOG, "12163"):      # EUR (inglés o español) para probar
            yield r


def main():
    cfg = json.load(open(os.path.join(ROOT, "config", "juegos.json"), encoding="utf-8"))
    ids = cfg["juegos"]
    names_en = english_names(ids)
    aliases = {a: norm(n) for a, n in names_en.items() if a in set(ids)}
    by_name = {}
    for a, n in aliases.items():
        by_name.setdefault(n, a)
    steam_base = {}
    data = os.path.join(ROOT, "site", "data.json")
    if os.path.exists(data):
        for g in json.load(open(data, encoding="utf-8"))["games"]:
            if g.get("base"):
                steam_base[g["id"]] = g["base"]

    src = sys.argv[1] if len(sys.argv) > 1 else None
    items = items_from_file(src) if src else items_from_api()
    best, n = {}, 0
    for it in items:
        n += 1
        name = get(it, "Name")
        if not name or BAD.search(name):
            continue
        if get(it, "StockAvailability", "Stock Availability").lower() not in ("instock", "in stock", ""):
            continue
        pf, pv = platform_of(get(it, "Text3"))
        if not pf:
            continue
        cur = get(it, "Currency")
        if cur and cur.upper() != "EUR":
            continue
        try:
            price = round(float(get(it, "CurrentPrice", "Current Price")), 2)
        except ValueError:
            continue
        url = get(it, "Url")
        if price <= 0 or not url:
            continue
        core, edition = split_name(name)
        c = norm(core)
        a = by_name.get(c)
        if a is None:
            hits = [h for h in by_name if close(c, h)]
            a = by_name[hits[0]] if hits else None
        if a is None:
            continue
        base = steam_base.get(a)
        if base and edition == "Standard" and price > base * MAX_VS_STEAM[pf]:
            continue
        rg = region_of(get(it, "Text1"))
        k = (a, pf, pv, edition, rg)
        if k not in best or price < best[k]["price"]:
            best[k] = dict(appid=a, store="loaded", platform=pf, version=pv, edition=edition, region=rg,
                           price=price, was=price, ends="", url=url)
    if n < 100 and not src:
        log(f"El catálogo parece incompleto ({n} productos). No toco feeds/loaded.json")
        sys.exit(0)
    rows = sorted(best.values(), key=lambda o: (o["appid"], o["platform"], o["version"], o["edition"], o["region"]))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    per = {}
    for o in rows:
        per[o["platform"]] = per.get(o["platform"], 0) + 1
    log(f"Loaded: {n} productos leídos · {len(rows)} ofertas para {len({o['appid'] for o in rows})} juegos · por plataforma: {per}")


if __name__ == "__main__":
    main()
