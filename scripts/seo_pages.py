#!/usr/bin/env python3
"""Páginas SEO de OfertaGG (las genera el robot después de update.py).

Lee site/data.json y crea páginas HTML normales (sin #) para que Google las encuentre:
  site/juego/<nombre>/index.html   una por juego, con sus precios por plataforma
  site/juegos/index.html           todos los juegos de la A a la Z
  site/<listas>/index.html         búsquedas típicas: juegos de PC baratos, claves de Xbox, géneros...
  site/sitemap.xml y site/llms.txt

Mismas reglas que la web: solo ofertas vivas; el precio principal es siempre Standard y en
una región que se activa en España (Global o Europa); "Resto del mundo" sale con aviso.
Nunca se inventa un descuento: el precio tachado solo aparece si es un descuento real.
"""
import datetime, html, json, os, re, shutil, unicodedata

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(R, "site")
# Cloudflare Web Analytics: cuenta visitas sin cookies (el token es público)
BEACON = '<!-- Cloudflare Web Analytics (sin cookies) --><script type=\'module\' src=\'https://static.cloudflareinsights.com/beacon.min.js\' data-cf-beacon=\'{"token": "8e40c011df3545b4a6baae2da6e9e786"}\'></script>'
URL = "https://ofertagg.com"
D = json.load(open(os.path.join(SITE, "data.json"), encoding="utf-8"))
GAMES = D["games"]
UPDATED = datetime.datetime.fromisoformat(D["updated"].replace("Z", "+00:00"))
TODAY = datetime.date.today()
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
FECHA = f"{UPDATED.day} de {MESES[UPDATED.month - 1]} de {UPDATED.year}"

STORES = {"steam": "Steam", "eneba": "Eneba", "instant": "Instant Gaming", "kinguin": "Kinguin",
          "loaded": "Loaded", "gamivo": "Gamivo", "fanatical": "Fanatical", "g2a": "G2A"}
PLATS = {"pc": ("PC", "Clave de Steam"), "xbox": ("Xbox", "Clave de Xbox"),
         "ps": ("PlayStation", "Código de PlayStation"), "switch": ("Switch", "Código de Nintendo eShop")}
PF_ORDER = ["pc", "xbox", "ps", "switch"]
REGION_OK = {"Global": True, "Europa": True, "Resto del mundo": False}

esc = lambda s: html.escape(str(s or ""), quote=True)
def eur(n): return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:70] or "juego"
def alive(o):
    return not o.get("exp") or datetime.date.fromisoformat(o["exp"][:10]) >= TODAY
def is_deal(o):
    return o["p"] < o.get("was", o["p"]) and (o.get("official") or (o.get("exp") and alive(o)))
def offers(g): return [o for o in g.get("o", []) if alive(o)]
def best(g, pf):
    c = sorted((o for o in offers(g) if o.get("pf", "pc") == pf and o.get("ed") == "Standard" and REGION_OK.get(o.get("rg"))), key=lambda o: o["p"])
    return c[0] if c else None
def link(g, o):
    return o.get("url") or (f"https://store.steampowered.com/app/{g['id']}/" if o["s"] == "steam" else None)
def plats(g): return [k for k in PF_ORDER if any(o.get("pf", "pc") == k for o in offers(g))]
def join_es(xs): return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " y " + xs[-1]

# URLs estables y únicas
slugs, used = {}, set()
for g in sorted(GAMES, key=lambda g: g["id"]):
    s = slugify(g["n"])
    if s in used: s = f"{s}-{g['id']}"
    used.add(s); slugs[g["id"]] = s
gurl = lambda g: f"/juego/{slugs[g['id']]}/"

def card(g):
    b = best(g, "pc") or next((best(g, k) for k in PF_ORDER if best(g, k)), None)
    if g.get("free"): price = '<b class="pr">Gratis</b>'
    elif b: price = (f'<s>{eur(b["was"])}</s> ' if is_deal(b) else "") + f'<b class="pr">desde {eur(b["p"])}</b>'
    else: price = '<span class="mut">Sin precio ahora</span>'
    return (f'<a class="card" href="{gurl(g)}"><img loading="lazy" src="/img/{g["id"]}_h.webp" alt="{esc(g["n"])}" width="460" height="215">'
            f'<span class="cn">{esc(g["n"])}</span><span class="cp">{price}</span></a>')

def page(path, title, desc, body, ld=None, img=None):
    lds = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False, separators=(",", ":"))}</script>' for x in (ld or []))
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{URL}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="OfertaGG"><meta property="og:locale" content="es_ES">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{URL}{path}">
<meta property="og:image" content="{URL}{img or '/img/logo.png'}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/img/favicon.png"><link rel="stylesheet" href="/seo.css">{lds}
</head><body>
<header class="top"><div class="wrap row"><a class="logo" href="/"><img src="/img/logo_dark.png" alt="" width="36" height="36"><span>Oferta<em>GG</em></span></a>
<nav><a href="/juegos/">Juegos</a><a href="/juegos-pc-baratos/">PC baratos</a><a href="/#ofertas">Ofertas</a><a class="cta" href="/">Comparador</a></nav></div></header>
<main class="wrap">{body}</main>
<footer class="foot"><div class="wrap"><p><b>OfertaGG</b> · El mismo juego. Menos dinero. Comparamos precios de claves de juegos; no vendemos juegos. Algunos enlaces son de afiliado: si compras, la tienda nos da una comisión y a ti no te cuesta más.</p>
<p>Precios comprobados el {FECHA}. Pueden cambiar: confirma siempre el precio en la tienda.</p>
<p><a href="/juegos/">Todos los juegos</a> · <a href="/#aviso-afiliados">Aviso de afiliación</a> · <a href="/#privacidad">Privacidad</a> · <a href="/#contacto">Contacto</a></p></div></footer>
{BEACON}
</body></html>
"""
    d = os.path.join(SITE, path.strip("/"))
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(doc)
    PAGES.append(path); TITLES[path] = title.replace(" | OfertaGG", "")

# Empezar de cero (los juegos nunca se borran, pero si uno cambia de nombre no queda una página vieja)
# (también las listas de la ejecución anterior, apuntadas en site/.seo_pages.txt)
OLD = os.path.join(SITE, ".seo_pages.txt")
for sub in ["juego"] + (open(OLD, encoding="utf-8").read().split() if os.path.exists(OLD) else []):
    if re.fullmatch(r"[a-z0-9-]+", sub) and sub != "img":
        shutil.rmtree(os.path.join(SITE, sub), ignore_errors=True)
PAGES, TITLES = [], {}
by_genre = {}
for g in GAMES:
    for x in g.get("g", []): by_genre.setdefault(x, []).append(g)
# Nombre natural de cada género en la URL y el título ("juegos indie", no "juegos de indie")
GEN_NAME = {"Casual": "juegos casuales", "Indie": "juegos indie", "Multijugador": "juegos multijugador",
            "Cooperativo": "juegos cooperativos", "Mundo abierto": "juegos de mundo abierto", "Soulslike": "juegos soulslike",
            "RPG": "juegos RPG", "Simulación": "juegos de simulación"}
gen_name = lambda x: GEN_NAME.get(x, "juegos de " + x.lower())
gen_path = lambda x: "/" + slugify(gen_name(x)) + "/"
popular = lambda lst: sorted(lst, key=lambda g: -(g.get("rec") or 0))

# ---------- página de cada juego ----------
for g in GAMES:
    pfs = plats(g)
    pnames = [PLATS[k][0] for k in pfs] or ["PC"]
    rows, ld_offers = [], []
    for k in pfs:
        lst = sorted(offers(g), key=lambda o: (not REGION_OK.get(o.get("rg")), o.get("ed") != "Standard", o["p"]))
        lst = [o for o in lst if o.get("pf", "pc") == k][:8]
        trs = []
        for o in lst:
            ok = REGION_OK.get(o.get("rg"))
            u = link(g, o)
            btn = f'<a class="buy" href="{esc(u)}" rel="nofollow sponsored noopener" target="_blank">Ir a {esc(STORES.get(o["s"], o["s"]))}</a>' if u else ""
            reg = esc(o.get("rg")) if ok else f'<span class="bad">{esc(o.get("rg"))} · no se activa en España</span>'
            was = f'<s>{eur(o["was"])}</s> ' if is_deal(o) else ""
            trs.append(f'<tr><td><b>{esc(STORES.get(o["s"], o["s"]))}</b><small>{esc(o.get("pv"))}</small></td><td>{esc(o.get("ed"))}</td><td>{reg}</td><td class="num">{was}<b>{eur(o["p"])}</b></td><td>{btn}</td></tr>')
            if ok and o.get("ed") == "Standard" and u: ld_offers.append(o)
        b = best(g, k)
        head = f'desde <b>{eur(b["p"])}</b> en {esc(STORES.get(b["s"], b["s"]))}' if b else "solo en otras regiones ahora mismo"
        rows.append(f'<section class="pf"><h2>{PLATS[k][0]} <span>· {PLATS[k][1]} · {head}</span></h2><div class="tw"><table><thead><tr><th>Tienda</th><th>Edición</th><th>Región</th><th>Precio</th><th></th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></section>')
    bpc = best(g, "pc") or next((best(g, k) for k in PF_ORDER if best(g, k)), None)
    nstores = len({o["s"] for o in offers(g)})
    if g.get("free"):
        title = f"{g['n']}: ¿es gratis? Dónde descargarlo | OfertaGG"
        desc = f"{g['n']} es gratis para jugar. Te decimos dónde descargarlo y el precio de sus ediciones en {join_es(pnames)}."
    else:
        title = f"{g['n']}: precio más barato en {join_es(pnames)} | OfertaGG"
        desc = (f"Compara el precio de {g['n']} en {nstores} tienda{'s' if nstores != 1 else ''}. "
                + (f"{PLATS[bpc.get('pf','pc')][1]} desde {eur(bpc['p'])} en {STORES.get(bpc['s'], bpc['s'])}. " if bpc else "")
                + "Solo regiones que se activan en España.")
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "OfertaGG", "item": URL + "/"},
        {"@type": "ListItem", "position": 2, "name": "Juegos", "item": URL + "/juegos/"},
        {"@type": "ListItem", "position": 3, "name": g["n"], "item": URL + gurl(g)}]}]
    if ld_offers:
        ps = [o["p"] for o in ld_offers]
        ld.append({"@context": "https://schema.org", "@type": "Product", "name": g["n"], "image": f"{URL}/img/{g['id']}_h.webp",
                   "description": html.unescape(g.get("sd") or "")[:300], "brand": {"@type": "Brand", "name": (g.get("pub") or g.get("dev") or ["—"])[0]},
                   "category": "Videojuegos", "offers": {"@type": "AggregateOffer", "priceCurrency": "EUR", "lowPrice": f"{min(ps):.2f}",
                   "highPrice": f"{max(ps):.2f}", "offerCount": len(ld_offers), "availability": "https://schema.org/InStock"}})
    rel = [x for x in popular(by_genre.get((g.get("g") or [""])[0], [])) if x["id"] != g["id"]][:6]
    facts = []
    if g.get("dev"): facts.append(f"<li><b>Desarrollador:</b> {esc(', '.join(g['dev']))}</li>")
    if g.get("rel"): facts.append(f"<li><b>Lanzamiento:</b> {esc(g['rel'])}</li>")
    if g.get("g"): facts.append("<li><b>Género:</b> " + ", ".join(f'<a href="{gen_path(x)}">{esc(x)}</a>' if len(by_genre.get(x, [])) >= 6 and x != "Gratis" else esc(x) for x in g["g"]) + "</li>")
    if g.get("mc"): facts.append(f"<li><b>Metacritic:</b> {g['mc']}</li>")
    if g.get("rec"): facts.append(f"<li><b>Reseñas en Steam:</b> {g['rec']:,}".replace(",", ".") + "</li>")
    faq = []
    if bpc and not g.get("free"):
        faq.append((f"¿Dónde es más barato {g['n']}?", f"Ahora mismo, la {PLATS[bpc.get('pf','pc')][1].lower()} más barata que se activa en España está en {STORES.get(bpc['s'], bpc['s'])} por {eur(bpc['p'])} (edición Standard, región {bpc.get('rg')}). Precios comprobados el {FECHA}."))
    faq.append((f"¿En qué plataformas puedo comprar {g['n']}?", f"En OfertaGG comparamos {g['n']} para {join_es(pnames)}."))
    faq.append(("¿Las claves funcionan en España?", "Las claves Global y Europa se activan en España. Las de «Resto del mundo» no: las marcamos en rojo y nunca las usamos como precio principal."))
    ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    hero = ""
    if g.get("free"): hero = '<p class="big">Gratis para jugar</p>'
    elif bpc: hero = f'<p class="big">{("<s>" + eur(bpc["was"]) + "</s> ") if is_deal(bpc) else ""}<b>desde {eur(bpc["p"])}</b></p><p class="mut">{PLATS[bpc.get("pf","pc")][1]} · {esc(STORES.get(bpc["s"], bpc["s"]))} · región {esc(bpc.get("rg"))}</p>'
    body = f"""<nav class="crumbs"><a href="/">Inicio</a> › <a href="/juegos/">Juegos</a> › {esc(g['n'])}</nav>
<article class="game"><img class="hdr" src="/img/{g['id']}_h.webp" alt="{esc(g['n'])}" width="460" height="215">
<div><h1>{esc(g['n'])}: precio más barato</h1>{hero}
<a class="btn" href="/#juego-{g['id']}">Comparar ediciones y regiones →</a>
<p class="mut small">Precios del {FECHA} en {nstores} tienda{'s' if nstores != 1 else ''}.</p></div></article>
<p>{esc(html.unescape(g.get('sd') or ''))}</p>
{''.join(rows) or '<p class="mut">Ahora mismo no tenemos precios de este juego. Vuelve pronto.</p>'}
<h2>Datos del juego</h2><ul class="facts">{''.join(facts)}</ul>
<h2>Preguntas frecuentes</h2>{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}
{('<h2>Juegos parecidos</h2><div class="grid">' + ''.join(card(x) for x in rel) + '</div>') if rel else ''}"""
    page(gurl(g), title, desc, body, ld, f"/img/{g['id']}_h.webp")

# ---------- listas (búsquedas típicas) ----------
def list_page(path, h1, desc, lst, intro):
    if len(lst) < 3: return
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": h1, "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": URL + gurl(g), "name": g["n"]} for i, g in enumerate(lst[:50])]}]
    page(path, f"{h1} | OfertaGG", desc, f'<nav class="crumbs"><a href="/">Inicio</a> › {esc(h1)}</nav><h1>{esc(h1)}</h1><p class="lead">{intro}</p><div class="grid">{"".join(card(g) for g in lst)}</div>', ld, f"/img/{lst[0]['id']}_h.webp")

pc_price = lambda g: (best(g, "pc") or {}).get("p", 9e9)
cheap = lambda lim: sorted((g for g in GAMES if not g.get("free") and pc_price(g) <= lim), key=lambda g: (-(g.get("rec") or 0)))
list_page("/juegos-pc-baratos/", "Juegos de PC baratos: claves de Steam por menos de 10 €", f"Juegos de PC por menos de 10 € con clave de Steam que se activa en España. Precios comparados el {FECHA}.", cheap(10), "Claves de Steam por menos de 10 €, ordenadas por popularidad. Solo regiones que se activan en España.")
list_page("/juegos-pc-menos-de-5-euros/", "Juegos de PC por menos de 5 €", f"Claves de Steam por menos de 5 € que funcionan en España ({FECHA}).", cheap(5), "Los juegos más baratos del catálogo: claves de Steam por menos de 5 €.")
list_page("/claves-steam-baratas/", "Claves de Steam baratas", "Compara precios de claves de Steam en varias tiendas y compra la más barata que se activa en España.", sorted((g for g in GAMES if best(g, "pc") and not g.get("free")), key=lambda g: -(g.get("rec") or 0)), "Los juegos más populares con su clave de Steam más barata en tiendas de claves.")
for k, path, h1 in [("xbox", "/claves-xbox-baratas/", "Claves de Xbox baratas"), ("ps", "/juegos-playstation-baratos/", "Juegos de PlayStation baratos"), ("switch", "/juegos-switch-baratos/", "Juegos de Switch baratos")]:
    lst = sorted((g for g in GAMES if best(g, k)), key=lambda g: best(g, k)["p"])
    list_page(path, h1, f"{h1}: comparamos precios de códigos para {PLATS[k][0]} que se activan en España.", lst, f"{PLATS[k][1]} al mejor precio, solo en regiones que funcionan en España.")
list_page("/juegos-gratis/", "Juegos gratis para PC", "Juegos gratis para jugar en PC (Free to Play).", [g for g in GAMES if g.get("free")], "Juegos gratuitos para jugar en PC.")
for gen, lst in sorted(by_genre.items()):
    if len(lst) >= 6 and gen != "Gratis":
        t = gen_name(gen); t = t[0].upper() + t[1:] + " baratos"
        list_page(gen_path(gen), t, f"{t}: los mejores al mejor precio en PC, Xbox, PlayStation y Switch.", popular(lst), f"{esc(t)}, ordenados por popularidad, con su precio más barato.")

# ---------- todos los juegos (A-Z) ----------
az = {}
for g in sorted(GAMES, key=lambda g: slugify(g["n"])):
    c = slugify(g["n"])[:1].upper()
    az.setdefault(c if c.isalpha() else "#", []).append(g)
body = '<nav class="crumbs"><a href="/">Inicio</a> › Juegos</nav><h1>Todos los juegos</h1><p class="lead">Precios de ' + str(len(GAMES)) + ' juegos para PC, Xbox, PlayStation y Switch.</p>'
body += '<p class="chips">' + "".join(f'<a href="{p}">{t}</a>' for p, t in [("/juegos-pc-baratos/", "PC por menos de 10 €"), ("/juegos-pc-menos-de-5-euros/", "Menos de 5 €"), ("/claves-xbox-baratas/", "Xbox"), ("/juegos-playstation-baratos/", "PlayStation"), ("/juegos-switch-baratos/", "Switch")] if p in PAGES)
body += "".join(f'<a href="{gen_path(x)}">{esc(x)}</a>' for x in sorted(by_genre) if gen_path(x) in PAGES) + "</p>"
body += "".join(f'<h2 id="l-{k}">{k}</h2><ul class="az">' + "".join(f'<li><a href="{gurl(g)}">{esc(g["n"])}</a></li>' for g in v) + "</ul>" for k, v in az.items())
page("/juegos/", "Todos los juegos y sus precios | OfertaGG", f"Lista de los {len(GAMES)} juegos que compara OfertaGG, con su precio más barato en PC, Xbox, PlayStation y Switch.", body)

# ---------- CSS, sitemap y llms.txt ----------
shutil.copyfile(os.path.join(R, "src", "seo.css"), os.path.join(SITE, "seo.css"))
lastmod = UPDATED.date().isoformat()
urls = [("/", "1.0")] + [(p, "0.8" if not p.startswith("/juego/") else "0.6") for p in PAGES]
open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(f"  <url><loc>{URL}{p}</loc><lastmod>{lastmod}</lastmod><priority>{pr}</priority></url>" for p, pr in urls) + "\n</urlset>\n")
top = sorted((g for g in GAMES if best(g, "pc")), key=lambda g: -(g.get("rec") or 0))[:30]
open(os.path.join(SITE, "llms.txt"), "w", encoding="utf-8").write(
    f"# OfertaGG\n\n> Comparador de precios de claves de videojuegos en español (PC/Steam, Xbox, PlayStation y Switch). Compara Steam con tiendas de claves como Kinguin y solo usa como precio principal regiones que se activan en España (Global y Europa). Eslogan: «El mismo juego. Menos dinero.»\n\n"
    f"Precios comprobados el {FECHA}. {len(GAMES)} juegos.\n\n## Páginas\n- [Todos los juegos]({URL}/juegos/)\n"
    + "".join(f"- [{TITLES[p]}]({URL}{p})\n" for p in PAGES if not p.startswith("/juego/") and p != "/juegos/")
    + "\n## Juegos populares (precio más barato de la clave de Steam)\n"
    + "".join(f"- [{g['n']}]({URL}{gurl(g)}): desde {eur(best(g, 'pc')['p'])} en {STORES.get(best(g, 'pc')['s'])}\n" for g in top))
open(OLD, "w", encoding="utf-8").write("\n".join(p.strip("/") for p in PAGES if not p.startswith("/juego/")))
print(f"Páginas SEO: {len(PAGES)} ({sum(p.startswith('/juego/') for p in PAGES)} juegos)")
