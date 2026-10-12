# OfertaGG

Comparador de precios de videojuegos para PC con enlaces de afiliado.

## Cómo funciona

```
GitHub (código + datos)  ──►  Netlify (publica la web)
   ▲
   └── Robot (GitHub Actions)
         · cada día: quita ofertas caducadas y publica al momento
           las ofertas nuevas de los juegos populares
         · cada lunes: revisión completa del catálogo
```

- **Los juegos nunca se borran.** Solo se quitan las ofertas que caducan o que la tienda ya no tiene. Si un juego no tiene ofertas, se muestra el precio normal de cada tienda.
- **Las ofertas nuevas en juegos populares** salen arriba del todo en la portada ("Nuevas ofertas en juegos populares") y en el carrusel, con la etiqueta "Nueva oferta" durante 7 días.
- Las ofertas con fecha de fin también desaparecen solas en la web en cuanto caducan, aunque el robot no haya pasado.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `site/` | La web que se publica (`index.html`, `data.json`, `img/`) |
| `config/juegos.json` | La lista de juegos. **Para añadir uno, pon su número de Steam.** |
| `feeds/` | Las ofertas de cada tienda afiliada (un archivo `.json` por tienda) |
| `scripts/update.py` | El robot que lo junta todo y genera `site/data.json` |
| `scripts/demo_feeds.py` | Precios de ejemplo. Se borra cuando lleguen los feeds reales |
| `src/` | El diseño de la web. Si lo cambias, ejecuta `python scripts/build_page.py` |
| `.github/workflows/` | El horario del robot |

## Puesta en marcha (una sola vez)

1. Crea una cuenta en **github.com** y un repositorio nuevo llamado `ofertagg` (privado o público).
2. En el repositorio, pulsa **Add file → Upload files** y arrastra **todo el contenido** de esta carpeta, incluida la carpeta oculta `.github`. Si tu ordenador la oculta, súbela aparte desde **Add file → Create new file**, con el nombre `.github/workflows/actualizar-ofertas.yml` y pegando su contenido.
3. En GitHub: **Settings → Actions → General → Workflow permissions →** marca **Read and write permissions** y guarda.
4. En **app.netlify.com**: **Add new site → Import an existing project → GitHub →** elige `ofertagg`. Netlify lee `netlify.toml` y publica la carpeta `site` solo.
5. Prueba el robot: en GitHub, **Actions → Actualizar ofertas → Run workflow**. En unos minutos verás un cambio nuevo ("Ofertas actualizadas…") y Netlify publicará la web.

A partir de ahí no tienes que hacer nada: el robot se ejecuta solo cada día y cada lunes.

## Cuando te aprueben un afiliado

Cada tienda da sus precios en un archivo o enlace (el "feed"). El robot espera en `feeds/<tienda>.json` una lista así:

```json
[{"appid": 1091500, "store": "eneba", "edition": "Standard", "region": "Global",
  "price": 35.25, "was": 59.99, "ends": "2026-10-20",
  "url": "https://...tu enlace de afiliado..."}]
```

- `store`: steam, eneba, instant, kinguin, loaded, gamivo o fanatical
- `region`: Global, Europa o Resto del mundo
- `ends`: fecha de fin de la oferta (vacío si es precio normal)
- `url`: tu enlace de afiliado; el botón "Ir a comprar" lleva ahí

Hay que hacer un pequeño script por tienda que descargue su feed y lo convierta a este formato. Después se borra `feeds/demo.json` y desaparece el aviso de "Versión de demostración".

## Probarlo en tu ordenador

```
pip install pillow
python scripts/update.py            # completo
python scripts/update.py --diario   # solo ofertas
cd site && python -m http.server    # abre http://localhost:8000
```
