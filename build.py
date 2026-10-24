#!/usr/bin/env python3
"""Generador estático de Grano y Taza.

  python3 build.py            -> genera la web en _site/ (para GitHub Pages)
  python3 build.py --preview  -> genera _preview/ con enlaces relativos (vista previa)

Apartados: content/guias/, content/resenas/, content/blog/ (cada .md es una página).
Catálogo de productos: data/productos.yaml (alimenta /productos/ y la portada).

Sintaxis extra en los .md:
  [texto](amazon:Nombre+del+producto)   -> búsqueda en Amazon con tu ID
  [texto](amazon-dp:B0XXXXXXX)          -> ficha concreta (ASIN) con tu ID
  [texto](catalogo:molinillo)           -> cuadrícula de productos filtrada por categoría
  ::: producto ... :::                  -> ficha de producto (ver README)
"""
import datetime as dt
import html
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

import markdown
import yaml
from zoneinfo import ZoneInfo

ROOT = Path(__file__).parent
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("_preview" if PREVIEW else "_site")
CFG = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
CAT = yaml.safe_load((ROOT / "data" / "productos.yaml").read_text(encoding="utf-8"))
CATEGORIAS = CAT["categorias"]
PRODUCTOS = CAT["productos"]
BYID = {p["id"]: p for p in PRODUCTOS}
BYNAME = {p["nombre"].lower(): p for p in PRODUCTOS}


def load_amazon():
    """Datos de la Creators API (data/amazon.json). Solo se usan si tienen menos de 24 h."""
    f = ROOT / "data" / "amazon.json"
    if not f.exists():
        return None, {}
    data = json.loads(f.read_text(encoding="utf-8"))
    when = dt.datetime.fromisoformat(data["actualizado"])
    if dt.datetime.now(dt.timezone.utc) - when > dt.timedelta(hours=24):
        return None, {}
    return when.astimezone(ZoneInfo("Europe/Madrid")), data.get("items", {})


API_TIME, API_ITEMS = load_amazon()
for _p in PRODUCTOS:
    _d = API_ITEMS.get(_p["id"])
    if _d:
        _p["api"] = _d
        if _d.get("precio"):
            _p["precio"] = float(_d["precio"])
PRICE_NOTE = (f"Precios de Amazon.es actualizados el {API_TIME:%d/%m/%Y} a las {API_TIME:%H:%M}. "
              "El precio y la disponibilidad pueden cambiar; el que aparezca en Amazon.es en el "
              "momento de la compra es el que se aplica.") if API_TIME else ""
BASE = "" if PREVIEW else CFG["baseurl"].rstrip("/")
E = html.escape

GAMAS = {"basica": "Gama de entrada", "media": "Gama media", "alta": "Gama alta"}
DISCLOSURE = ("En calidad de Afiliado de Amazon, obtengo ingresos por las compras "
              "adscritas que cumplen los requisitos aplicables.")
SECTIONS = {
    "guias": {"title": "Guías de compra", "nav": "Guías", "item": "Guía de compra",
              "intro": "Comparativas por presupuesto para elegir cafetera, molinillo y accesorios sin perderte entre cientos de modelos."},
    "resenas": {"title": "Reseñas", "nav": "Reseñas", "item": "Reseña",
                "intro": "Análisis a fondo de un solo producto: qué hace bien, qué no, y para quién merece la pena."},
    "blog": {"title": "Blog", "nav": "Blog", "item": "Blog",
             "intro": "Técnica, trucos y explicaciones para sacar mejor café de lo que ya tienes en casa."},
}
NAV = [("guias", "Guías"), ("resenas", "Reseñas"), ("productos", "Productos"), ("blog", "Blog")]
AMAZON_QUERY = {
    "espresso": "cafetera espresso", "superautomatica": "cafetera superautomatica",
    "molinillo": "molinillo cafe", "italiana": "cafetera italiana", "cafe": "cafe en grano",
    "filtro": "cafetera filtro manual", "accesorio": "accesorios cafe barista",
}
RANGOS = [(0, 50, "Menos de 50 €"), (50, 150, "50–150 €"), (150, 300, "150–300 €"),
          (300, 600, "300–600 €"), (600, 1000, "600–1.000 €"), (1000, 10**6, "Más de 1.000 €")]

INK, CREAM, RED, CARAMEL, STEEL, STEEL_D, KRAFT, KRAFT_D, WHITE = (
    "#241813", "#F6F1E7", "#A8202C", "#E2B57A", "#C9C3B8", "#9B948A", "#C99A5B", "#A87C44", "#FFFFFF")
SHADOW = '<ellipse cx="200" cy="272" rx="130" ry="12" fill="#241813" opacity=".08"/>'
CUP_S = (f'<path d="M172 214 h56 v18 a18 18 0 0 1 -18 18 h-20 a18 18 0 0 1 -18 -18 z" fill="{WHITE}"/>'
         f'<path d="M228 220 h6 a9 9 0 0 1 0 18 h-6" fill="none" stroke="{WHITE}" stroke-width="5"/>'
         f'<rect x="176" y="214" width="48" height="5" rx="2.5" fill="{CARAMEL}"/>')

ICONS = {  # ilustraciones planas por categoría (no se usan fotos de Amazon sin su API)
    "espresso": SHADOW + (
        f'<rect x="112" y="40" width="176" height="18" rx="7" fill="{STEEL}"/>'
        f'<rect x="104" y="54" width="192" height="214" rx="16" fill="{CREAM}"/>'
        f'<rect x="120" y="70" width="160" height="44" rx="8" fill="{INK}"/>'
        f'<circle cx="146" cy="92" r="11" fill="{STEEL}"/><circle cx="254" cy="92" r="11" fill="{STEEL}"/>'
        f'<rect x="182" y="86" width="36" height="11" rx="5.5" fill="{RED}"/>'
        f'<rect x="168" y="122" width="64" height="22" rx="5" fill="{STEEL}"/>'
        f'<rect x="162" y="144" width="76" height="14" rx="6" fill="{INK}"/>'
        f'<rect x="228" y="147" width="96" height="9" rx="4.5" fill="{INK}"/>'
        f'<rect x="186" y="158" width="4" height="52" rx="2" fill="{CARAMEL}"/>'
        f'<rect x="210" y="158" width="4" height="52" rx="2" fill="{CARAMEL}"/>'
        + CUP_S +
        f'<rect x="116" y="246" width="168" height="16" rx="5" fill="{STEEL}"/>'),
    "superautomatica": SHADOW + (
        f'<rect x="124" y="30" width="152" height="238" rx="22" fill="{CREAM}"/>'
        f'<rect x="124" y="30" width="152" height="30" rx="14" fill="{STEEL}"/>'
        f'<rect x="146" y="76" width="108" height="46" rx="8" fill="{INK}"/>'
        f'<rect x="156" y="88" width="40" height="8" rx="4" fill="{CARAMEL}"/>'
        f'<rect x="156" y="102" width="62" height="6" rx="3" fill="{STEEL_D}"/>'
        f'<rect x="180" y="138" width="40" height="22" rx="6" fill="{INK}"/>'
        f'<rect x="190" y="160" width="4" height="50" rx="2" fill="{CARAMEL}"/>'
        f'<rect x="206" y="160" width="4" height="50" rx="2" fill="{CARAMEL}"/>'
        + CUP_S +
        f'<rect x="138" y="248" width="124" height="14" rx="5" fill="{STEEL}"/>'),
    "molinillo": SHADOW + (
        f'<path d="M150 70 a50 22 0 0 1 100 0 v54 h-100 z" fill="{WHITE}" opacity=".55"/>'
        f'<rect x="150" y="104" width="100" height="22" fill="#3A2418"/>'
        f'<ellipse cx="200" cy="104" rx="50" ry="8" fill="#5A3826"/>'
        f'<rect x="140" y="124" width="120" height="146" rx="22" fill="{INK}"/>'
        f'<rect x="156" y="140" width="88" height="6" rx="3" fill="{STEEL_D}"/>'
        f'<rect x="185" y="176" width="30" height="50" rx="15" fill="{STEEL}"/>'
        f'<circle cx="200" cy="192" r="7" fill="{RED}"/>'),
    "italiana": SHADOW + (
        f'<path d="M150 70 h100 l-14 72 h-72 z" fill="{STEEL}"/>'
        f'<path d="M150 70 h100 l-4 14 h-92 z" fill="{STEEL_D}"/>'
        f'<rect x="196" y="56" width="8" height="14" rx="4" fill="{INK}"/>'
        f'<rect x="160" y="142" width="80" height="12" rx="3" fill="{STEEL_D}"/>'
        f'<path d="M164 154 h72 l14 114 h-100 z" fill="{STEEL}"/>'
        f'<path d="M250 84 c40 6 40 50 4 56" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
        f'<path d="M150 74 l-18 -8" stroke="{STEEL_D}" stroke-width="8" stroke-linecap="round"/>'),
    "filtro": SHADOW + (
        f'<path d="M140 58 h120 l-36 70 h-48 z" fill="{RED}"/>'
        f'<rect x="132" y="50" width="136" height="12" rx="6" fill="{RED}"/>'
        f'<rect x="168" y="128" width="64" height="10" rx="4" fill="{RED}"/>'
        f'<path d="M150 140 h100 l12 120 a10 10 0 0 1 -10 10 h-104 a10 10 0 0 1 -10 -10 z" fill="{WHITE}" opacity=".7"/>'
        f'<path d="M152 200 h96 l6 58 a8 8 0 0 1 -8 8 h-92 a8 8 0 0 1 -8 -8 z" fill="#6B3E24"/>'),
    "cafe": SHADOW + (
        f'<path d="M140 60 h120 l14 208 h-148 z" fill="{KRAFT}"/>'
        f'<path d="M144 40 h112 l4 22 h-120 z" fill="{KRAFT_D}"/>'
        f'<rect x="160" y="128" width="80" height="80" rx="12" fill="{CREAM}"/>'
        f'<ellipse cx="200" cy="168" rx="16" ry="22" transform="rotate(25 200 168)" fill="#6B3E24"/>'
        f'<path d="M193 150 c11 9 -4 22 6 36" fill="none" stroke="{CREAM}" stroke-width="4" stroke-linecap="round"/>'),
    "accesorio": SHADOW + (
        f'<rect x="110" y="236" width="180" height="30" rx="8" fill="{INK}"/>'
        f'<rect x="170" y="244" width="60" height="12" rx="3" fill="{CARAMEL}"/>'
        f'<path d="M150 236 v-90 a40 40 0 0 1 40 -40 h20 a40 40 0 0 1 40 40 v90 z" fill="{STEEL}"/>'
        f'<path d="M150 170 c-40 -10 -48 -50 -62 -70" fill="none" stroke="{STEEL_D}" stroke-width="10" stroke-linecap="round"/>'
        f'<rect x="186" y="92" width="28" height="14" rx="7" fill="{INK}"/>'
        f'<path d="M250 140 c26 0 26 60 0 60" fill="none" stroke="{INK}" stroke-width="12"/>'),
}


def icon(cat):
    return (f'<svg viewBox="0 0 400 300" aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
            f'{ICONS.get(cat, ICONS["espresso"])}</svg>')


def tema_of(p):
    """Ilustración de la tarjeta de un artículo: campo 'tema', producto de la reseña o pistas del slug."""
    if p.get("tema"):
        return p["tema"]
    prod = BYID.get(p.get("producto"))
    if prod:
        return prod["categoria"]
    slug = p.get("slug", "")
    for key, cat in (("molinillo", "molinillo"), ("superautomat", "superautomatica"), ("italiana", "italiana"),
                     ("cafes-en-grano", "cafe"), ("que-cafetera", "filtro")):
        if key in slug:
            return cat
    return "espresso"


def entry_cards(pages, limit=None):
    items = []
    for p in (pages[:limit] if limit else pages):
        sec = SECTIONS[p["section"]]
        t = tema_of(p)
        items.append(
            f'<li class="ecard"><a href="{link(p["slug"])}">'
            f'<span class="ethumb cat-{t}">{icon(t)}</span>'
            f'<span class="kind">{sec["item"]}</span>'
            f'<strong>{E(p["title"])}</strong>'
            f'<span class="sum">{E(p.get("summary", ""))}</span></a></li>')
    return f'<ul class="ecards">{"".join(items)}</ul>'


def excerpt(p, limit=620):
    """Resumen largo en texto plano: entradilla + primeros párrafos del artículo, cortado en una frase."""
    parts = [p.get("lede") or p.get("summary") or ""]
    body = re.sub(r"<!--.*?-->", "", p.get("body_md", ""), flags=re.S)
    body = re.sub(r"^:::.*?^:::", "", body, flags=re.S | re.M)
    for block in re.split(r"\n\s*\n", body):
        b = block.strip()
        if not b or b[0] in "#|<-*>!" or b[:2].rstrip(".").isdigit():
            continue
        b = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", b)
        b = re.sub(r"[*_`]", "", b).replace("\n", " ")
        if b.endswith(":"):
            continue
        parts.append(b)
        if sum(len(x) for x in parts) > limit:
            break
    text = " ".join(x for x in parts if x)
    if len(text) > limit:
        cut = text[:limit]
        dot = cut.rfind(". ")
        text = cut[:dot + 1] if dot > limit * .5 else cut.rsplit(" ", 1)[0] + "…"
    return text


def story_rows(pages, limit=None):
    """Artículos de lectura (blog): ilustración a un lado y resumen largo al otro, alternando."""
    rows = []
    for i, p in enumerate(pages[:limit] if limit else pages):
        t = tema_of(p)
        rows.append(
            f'<article class="story{" flip" if i % 2 else ""}">'
            f'<a class="story-art cat-{t}" href="{link(p["slug"])}" tabindex="-1" aria-hidden="true">{icon(t)}</a>'
            f'<div class="story-text"><p class="kind">{SECTIONS[p["section"]]["item"]} · {fecha_es(p.get("updated"))}</p>'
            f'<h3><a href="{link(p["slug"])}">{E(p["title"])}</a></h3>'
            f'<p class="story-sum">{E(excerpt(p))}</p>'
            f'<p><a class="ghost" href="{link(p["slug"])}">Seguir leyendo</a></p></div></article>')
    return f'<div class="stories">{"".join(rows)}</div>'


def guide_feature(pages, limit=None):
    """Guías: una destacada grande con el texto sobre color y el resto en lista numerada."""
    pages = pages[:limit] if limit else pages
    if not pages:
        return ""
    lead, rest = pages[0], pages[1:]
    t = tema_of(lead)
    big = (f'<a class="gfeat cat-{t}" href="{link(lead["slug"])}">'
           f'<span class="gfeat-text"><span class="kind">Guía destacada</span>'
           f'<strong>{E(lead["title"])}</strong><span class="sum">{E(lead.get("summary", ""))}</span>'
           f'<span class="gbtn">Leer la guía</span></span>'
           f'<span class="gfeat-art">{icon(t)}</span></a>')
    items = "".join(
        f'<li><a href="{link(p["slug"])}"><span class="gnum">{i:02d}</span>'
        f'<span class="gbody"><strong>{E(p["title"])}</strong><span class="sum">{E(p.get("summary", ""))}</span></span></a></li>'
        for i, p in enumerate(rest, 1))
    return f'<div class="guides">{big}<ol class="glist">{items}</ol></div>'


def review_rows(pages, limit=None):
    """Reseñas: filas horizontales con nota y veredicto, distintas de las tarjetas de compra."""
    rows = []
    for p in (pages[:limit] if limit else pages):
        t = tema_of(p)
        prod = BYID.get(p.get("producto")) or {}
        nota = p.get("nota")
        stars = ""
        if nota:
            n = int(float(nota))
            stars = f'<span class="stars" aria-label="Mi nota: {nota} de 5">{"★" * n}{"☆" * (5 - n)}</span>'
        mine = '<span class="badge-mine">La uso en casa</span>' if prod.get("propio") else '<span class="badge-an">Análisis</span>'
        ver = p.get("veredicto") or p.get("summary", "")
        if len(ver) > 260:
            ver = ver[:260].rsplit(" ", 1)[0] + "…"
        rows.append(
            f'<li class="rrow"><a href="{link(p["slug"])}">'
            f'<span class="rthumb cat-{t}">{icon(t)}</span>'
            f'<span class="rbody"><span class="rmeta">{mine}{stars}</span>'
            f'<strong>{E(p["title"])}</strong><span class="sum">{E(ver)}</span></span>'
            f'<span class="rgo" aria-hidden="true">→</span></a></li>')
    return f'<ul class="rrows">{"".join(rows)}</ul>'


def price_html(p):
    d = p.get("api") or {}
    if d.get("precio_texto"):
        return (f'<span class="prange real">{E(d["precio_texto"])}</span>'
                f'<small class="pts">a las {API_TIME:%H:%M}</small>')
    return f'<span class="prange">{rango(p["precio"])}</span>'


def media_html(p, cls, linked=True):
    """Imagen del producto: foto de la API de Amazon > foto propia (campo foto) > ilustración.
    Con linked=True la imagen entera lleva a Amazon con el ID de afiliado."""
    d = p.get("api") or {}
    src = d.get("imagen") or (f'{BASE}/{p["foto"].lstrip("/")}' if p.get("foto") else None)
    if src:
        inner = (f'<img src="{E(src)}" alt="{E(p["nombre"])}" loading="lazy" referrerpolicy="no-referrer">')
        klass = f"{cls} photo"
    else:
        inner, klass = icon(p["categoria"]), f'{cls} cat-{p["categoria"]}'
    if linked:
        return (f'<a class="{klass}" href="{E(prod_url(p))}" {SPONSORED} '
                f'aria-label="Ver {E(p["nombre"])} en Amazon">{inner}</a>')
    return f'<div class="{klass}">{inner}</div>'


def rango(precio):
    for lo, hi, label in RANGOS:
        if lo <= precio < hi:
            return label
    return ""


def amazon_url(query=None, asin=None):
    d, tag = CFG["amazon_domain"], CFG["amazon_tag"]
    if asin:
        return f"https://{d}/dp/{asin}?tag={tag}"
    q = urllib.parse.quote_plus(query.replace("+", " "))
    return f"https://{d}/s?k={q}&tag={tag}"


def prod_url(p):
    if p.get("api", {}).get("url"):
        return p["api"]["url"]
    return amazon_url(asin=p["asin"]) if p.get("asin") else amazon_url(p.get("buscar", p["nombre"]))


def link(path):
    path = path.strip("/")
    return f"{BASE}/{path}/" if path else f"{BASE}/"


def md(text):
    return markdown.markdown(text, extensions=["tables", "toc", "attr_list", "smarty"],
                             extension_configs={"toc": {"permalink": False},
                                                "smarty": {"smart_angled_quotes": True}})


SPONSORED = 'rel="sponsored nofollow noopener" target="_blank"'


# ---------- fichas y tarjetas ----------

def render_product(block):
    p = yaml.safe_load(block)
    base = BYID.get(p.get("id")) or BYNAME.get(str(p.get("nombre", "")).lower())
    if base:
        p = {**base, **p}
    gama = p.get("gama", "media")
    pros = "".join(f"<li>{E(x)}</li>" for x in p.get("pros", []))
    cons = "".join(f"<li>{E(x)}</li>" for x in p.get("contras", []))
    review = (f' <a class="more" href="{link(p["resena"])}">Leer la reseña completa</a>'
              if p.get("resena") else "")
    return f"""
<section class="product{' has-media' if p.get('categoria') else ''}" data-gama="{gama}">
  {media_html(p, "product-media") if p.get("categoria") else ""}
  <div class="product-main">
  <header class="product-head">
    <p class="gama"><span class="roast roast-{gama}" aria-hidden="true"></span>{GAMAS.get(gama, gama)}</p>
    <h3><a href="{E(prod_url(p))}" {SPONSORED}>{E(p['nombre'])}</a></h3>
    <p class="ideal">Ideal para: {E(p.get('ideal', ''))}</p>
  </header>
  <div class="product-body">{md(p.get('texto', ''))}</div>
  <div class="procon">
    <div><h4>Lo mejor</h4><ul class="pros">{pros}</ul></div>
    <div><h4>A tener en cuenta</h4><ul class="cons">{cons}</ul></div>
  </div>
  <p class="actions">{price_html(p) if p.get("api") else ""}<a class="buy" href="{E(prod_url(p))}" {SPONSORED}>Ver precio en Amazon</a>{review}</p>
  </div>
</section>
"""


def card(p, heading="h3", nota=None):
    extra = ""
    if p.get("resena"):
        extra = f'<a class="more" href="{link(p["resena"])}">Leer reseña</a>'
    elif p.get("guia"):
        extra = f'<a class="more" href="{link(p["guia"])}">Ver en la guía</a>'
    gama = p.get("gama", "media")
    return f"""<li class="pcard" data-cat="{p['categoria']}" data-gama="{gama}" data-precio="{p['precio']}"
 data-rel="{p.get('relevancia', 50)}" data-fecha="{p.get('anadido', '')}" data-marca="{E(p.get('marca', ''))}"
 data-texto="{E((p['nombre'] + ' ' + p.get('marca', '') + ' ' + p.get('resumen', '')).lower())}">
  {media_html(p, "pimg")}
  {f'<p class="mine">{E(p.get("etiqueta", "Lo uso en casa"))}</p>' if p.get("propio") else ''}
  <p class="pcat">{E(CATEGORIAS.get(p['categoria'], ''))}</p>
  <{heading} class="pname"><a href="{E(prod_url(p))}" {SPONSORED}>{E(p['nombre'])}</a></{heading}>
  <p class="psum">{E(nota or p.get('resumen', ''))}</p>
  <p class="pmeta"><span class="roast roast-{gama}" aria-hidden="true"></span><span>{GAMAS[gama]}</span>{price_html(p)}</p>
  <p class="pactions"><a class="buy small" href="{E(prod_url(p))}" {SPONSORED}>Ver en Amazon</a>{extra}</p>
</li>"""


def catalog_html():
    counts = {c: sum(1 for p in PRODUCTOS if p["categoria"] == c) for c in CATEGORIAS}
    chips = '<label class="chip"><input type="radio" name="cat" value="" checked><span>Todos <small>{}</small></span></label>'.format(len(PRODUCTOS))
    chips += "".join(f'<label class="chip"><input type="radio" name="cat" value="{k}"><span>{E(v)} <small>{counts[k]}</small></span></label>'
                     for k, v in CATEGORIAS.items())
    rangos = '<option value="">Cualquier precio</option>' + "".join(
        f'<option value="{lo}-{hi}">{label}</option>' for lo, hi, label in RANGOS)
    marcas = '<option value="">Todas las marcas</option>' + "".join(
        f'<option>{E(m)}</option>' for m in sorted({p.get("marca", "") for p in PRODUCTOS}))
    cards = "".join(card(p) for p in sorted(PRODUCTOS, key=lambda p: -p.get("relevancia", 0)))
    amazon_cfg = json.dumps({"domain": CFG["amazon_domain"], "tag": CFG["amazon_tag"],
                             "queries": AMAZON_QUERY, "default": "cafetera"}, ensure_ascii=False)
    return f"""
<div class="catalog">
  <form class="filters" id="filtros" role="search" aria-label="Filtrar productos" onsubmit="return false">
    <label class="field"><span>Buscar en el catálogo</span><input type="search" name="q" placeholder="Marca o modelo"></label>
    <fieldset class="field"><legend>Categoría</legend><div class="chips">{chips}</div></fieldset>
    <label class="field"><span>Precio</span><select name="precio">{rangos}</select></label>
    <label class="field"><span>Gama</span><select name="gama"><option value="">Todas las gamas</option><option value="basica">Gama de entrada</option><option value="media">Gama media</option><option value="alta">Gama alta</option></select></label>
    <label class="field"><span>Marca</span><select name="marca">{marcas}</select></label>
    <button type="reset" class="reset">Quitar filtros</button>
  </form>
  <div class="results">
    <div class="resbar">
      <p id="contador" aria-live="polite">{len(PRODUCTOS)} productos</p>
      <label class="sort"><span>Ordenar por</span>
        <select name="orden" form="filtros">
          <option value="rel">Relevancia</option>
          <option value="fecha">Novedades</option>
          <option value="precio-asc">Precio: de menor a mayor</option>
          <option value="precio-desc">Precio: de mayor a menor</option>
          <option value="nombre">Nombre</option>
        </select></label>
    </div>
    {f'<p class="pricenote">{E(PRICE_NOTE)}</p>' if PRICE_NOTE else ''}
    <ul class="pgrid" id="rejilla">{cards}</ul>
    <div class="empty" id="vacio" hidden>
      <p><strong>Ningún producto del catálogo coincide con esos filtros.</strong></p>
      <p>Quita algún filtro o busca directamente en Amazon con el buscador de abajo.</p>
    </div>
    <section class="amazon-search" aria-labelledby="busca-amazon">
      <h2 id="busca-amazon">Buscar en Amazon</h2>
      <p>Lanza la búsqueda en Amazon.es con el orden y el rango de precio que elijas. Se abre en una pestaña nueva con los precios y las opiniones al día.</p>
      <form id="amazonForm" class="aform">
        <label class="field grow"><span>Qué buscas</span><input name="k" value="cafetera" required></label>
        <label class="field"><span>Ordenar Amazon por</span><select name="s">
          <option value="">Relevancia</option>
          <option value="price-asc-rank">Precio: más bajo</option>
          <option value="price-desc-rank">Precio: más alto</option>
          <option value="date-desc-rank">Novedades</option>
          <option value="review-rank">Mejor valorados</option>
        </select></label>
        <label class="field small"><span>Precio mín. (€)</span><input name="low" inputmode="numeric" pattern="[0-9]*"></label>
        <label class="field small"><span>Precio máx. (€)</span><input name="high" inputmode="numeric" pattern="[0-9]*"></label>
        <button class="buy" type="submit">Ver resultados en Amazon</button>
      </form>
      <p class="alink" hidden>Si no se ha abierto una pestaña nueva, <a id="amazonLink" href="#" {SPONSORED}>abre los resultados en Amazon</a>.</p>
    </section>
  </div>
</div>
<script>
(function () {{
  var AMZ = {amazon_cfg};
  var f = document.getElementById('filtros'), grid = document.getElementById('rejilla');
  var cards = Array.prototype.slice.call(grid.children), af = document.getElementById('amazonForm');
  var counter = document.getElementById('contador'), empty = document.getElementById('vacio');
  function val(n) {{ var el = f.elements[n]; return el ? (el.value || '') : ''; }}
  function cat() {{ var c = f.querySelector('input[name=cat]:checked'); return c ? c.value : ''; }}
  function apply(push) {{
    var q = val('q').trim().toLowerCase(), c = cat(), pr = val('precio'), g = val('gama'), m = val('marca');
    var lo = 0, hi = Infinity;
    if (pr) {{ lo = +pr.split('-')[0]; hi = +pr.split('-')[1]; }}
    var shown = 0;
    cards.forEach(function (el) {{
      var d = el.dataset, p = +d.precio;
      var ok = (!c || d.cat === c) && (!g || d.gama === g) && (!m || d.marca === m) &&
               p >= lo && p < hi && (!q || d.texto.indexOf(q) !== -1);
      el.hidden = !ok; if (ok) shown++;
    }});
    var o = document.querySelector('select[name=orden]').value;
    cards.slice().sort(function (a, b) {{
      var A = a.dataset, B = b.dataset;
      if (o === 'precio-asc') return A.precio - B.precio;
      if (o === 'precio-desc') return B.precio - A.precio;
      if (o === 'fecha') return (B.fecha > A.fecha) - (B.fecha < A.fecha) || B.rel - A.rel;
      if (o === 'nombre') return a.querySelector('.pname').textContent.localeCompare(b.querySelector('.pname').textContent, 'es');
      return B.rel - A.rel;
    }}).forEach(function (el) {{ grid.appendChild(el); }});
    counter.textContent = shown === 1 ? '1 producto' : shown + ' productos';
    empty.hidden = shown !== 0;
    // sincroniza el buscador de Amazon con los filtros
    af.elements.k.value = q || AMZ.queries[c] || AMZ['default'];
    af.elements.low.value = pr && lo > 0 ? lo : '';
    af.elements.high.value = pr && hi < 100000 ? hi : '';
    af.elements.s.value = o === 'precio-asc' ? 'price-asc-rank' : o === 'precio-desc' ? 'price-desc-rank' : o === 'fecha' ? 'date-desc-rank' : '';
    if (push) {{
      var sp = new URLSearchParams();
      if (c) sp.set('cat', c); if (pr) sp.set('precio', pr); if (g) sp.set('gama', g);
      if (m) sp.set('marca', m); if (q) sp.set('q', q); if (o !== 'rel') sp.set('orden', o);
      try {{ history.replaceState(null, '', sp.toString() ? '?' + sp : location.pathname); }} catch (e) {{}}
    }}
  }}
  var init = new URLSearchParams(location.search);
  ['precio', 'gama', 'marca', 'q'].forEach(function (k) {{ if (init.get(k)) f.elements[k].value = init.get(k); }});
  if (init.get('orden')) document.querySelector('select[name=orden]').value = init.get('orden');
  if (init.get('cat')) {{ var r = f.querySelector('input[name=cat][value="' + init.get('cat') + '"]'); if (r) r.checked = true; }}
  f.addEventListener('input', function () {{ apply(true); }});
  f.addEventListener('change', function () {{ apply(true); }});
  document.querySelector('select[name=orden]').addEventListener('change', function () {{ apply(true); }});
  f.addEventListener('reset', function () {{ setTimeout(function () {{ document.querySelector('select[name=orden]').value = 'rel'; apply(true); }}, 0); }});
  af.addEventListener('submit', function (e) {{
    e.preventDefault();
    var p = new URLSearchParams({{ k: af.elements.k.value.trim() || AMZ['default'] }});
    if (af.elements.s.value) p.set('s', af.elements.s.value);
    if (af.elements.low.value) p.set('low-price', af.elements.low.value);
    if (af.elements.high.value) p.set('high-price', af.elements.high.value);
    p.set('tag', AMZ.tag);
    var url = 'https://' + AMZ.domain + '/s?' + p.toString();
    var w = null;
    try {{ w = window.open(url, '_blank', 'noopener'); }} catch (err) {{}}
    var out = document.getElementById('amazonLink');
    out.href = url; out.parentNode.hidden = false;
  }});
  apply(false);
}})();
</script>"""


def entry_list(pages, compact=False):
    items = []
    for p in pages:
        sec = SECTIONS[p["section"]]
        date = p.get("updated")
        date_txt = f'<time datetime="{date}">{fecha_es(date)}</time>' if date else ""
        items.append(
            f'<li class="entry e-{p["section"]}"><a href="{link(p["slug"])}">'
            f'<span class="kind">{sec["item"]}</span>'
            f'<strong>{E(p["title"])}</strong>'
            f'<span class="sum">{E(p.get("summary", ""))}</span>'
            f'{"" if compact else date_txt}</a></li>')
    return f'<ul class="entries">{"".join(items)}</ul>'


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_es(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}" if hasattr(d, "month") else str(d)


def rating_html(nota):
    """Nota visible (Google exige que la puntuación marcada también se vea en la página)."""
    if not nota:
        return ""
    n = float(nota)
    full = int(n)
    half = n - full >= 0.5
    stars = "★" * full + ("⯪" if half else "") + "☆" * (5 - full - (1 if half else 0))
    txt = f"{n:g}".replace(".", ",")
    return (f'<p class="rating"><span class="stars" aria-hidden="true">{stars}</span>'
            f'<strong>Mi nota: {txt} de 5</strong></p>')


def review_box(meta):
    p = BYID.get(meta.get("producto"))
    if not p:
        return ""
    pros = "".join(f"<li>{E(x)}</li>" for x in meta.get("pros", []))
    cons = "".join(f"<li>{E(x)}</li>" for x in meta.get("contras", []))
    datos = "".join(f"<tr><th>{E(k)}</th><td>{E(str(v))}</td></tr>" for k, v in (meta.get("ficha") or {}).items())
    return f"""
<aside class="verdict" aria-label="Resumen de la reseña">
  {media_html(p, "vimg")}
  <div class="vbody">
    <p class="gama"><span class="roast roast-{p['gama']}" aria-hidden="true"></span>{GAMAS[p['gama']]}{price_html(p)}</p>
    <h2>Veredicto</h2>
    {rating_html(meta.get('nota'))}
    <p>{E(meta.get('veredicto', ''))}</p>
    <div class="procon"><div><h4>Lo mejor</h4><ul class="pros">{pros}</ul></div>
    <div><h4>A tener en cuenta</h4><ul class="cons">{cons}</ul></div></div>
    {f'<table class="ficha">{datos}</table>' if datos else ''}
    <p class="actions"><a class="buy" href="{E(prod_url(p))}" {SPONSORED}>Ver precio en Amazon</a></p>
  </div>
</aside>"""


# ---------- render ----------

def render_grid(block):
    """::: productos -> rejilla de tarjetas. Cada línea: un id del catálogo, o {id, nota}."""
    items = yaml.safe_load(block) or []
    cards = []
    for it in items:
        it = {"id": it} if isinstance(it, str) else it
        p = BYID.get(it["id"])
        if p:
            cards.append(card(p, nota=it.get("nota")))
        else:
            print(f"AVISO: producto '{it['id']}' no está en data/productos.yaml")
    return f'<ul class="pgrid inline">{"".join(cards)}</ul>'


def render_body(text):
    text = text.replace("{{base}}", BASE)
    parts, last = [], 0
    for m in re.finditer(r"^::: (productos|producto)\n(.*?)\n:::\s*$", text, flags=re.S | re.M):
        parts.append(md(text[last:m.start()]))
        parts.append(render_grid(m.group(2)) if m.group(1) == "productos" else render_product(m.group(2)))
        last = m.end()
    parts.append(md(text[last:]))
    out = "".join(parts)

    def fix(m):
        kind, val = m.group(1), html.unescape(m.group(2))
        if kind == "catalogo":
            return f'<a href="{link("productos")}?cat={E(val)}"'
        url = amazon_url(asin=val) if kind == "amazon-dp" else amazon_url(val)
        return f'<a href="{E(url)}" {SPONSORED}'
    out = re.sub(r'<a href="(amazon|amazon-dp|catalogo):([^"]+)"', fix, out)
    # cualquier enlace "Ver en Amazon" escrito en el texto se muestra como botón
    return re.sub(r'(<a href="[^"]+" rel="sponsored[^"]*" target="_blank")>(Ver en Amazon|Ver precio en Amazon)</a>',
                  r'\1 class="buy small">\2</a>', out)


def load_pages():
    pages = []
    for f in sorted((ROOT / "content").rglob("*.md")):
        raw = f.read_text(encoding="utf-8")
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm)
        rel = f.relative_to(ROOT / "content").with_suffix("")
        meta.setdefault("slug", "" if str(rel) == "index" else rel.as_posix())
        meta["section"] = rel.parts[0] if len(rel.parts) > 1 and rel.parts[0] in SECTIONS else None
        if meta["section"]:
            meta["layout"] = "article"
        meta["body_md"] = body
        pages.append(meta)
    # portadas de cada apartado
    for key, sec in SECTIONS.items():
        pages.append({"slug": key, "title": sec["title"], "description": sec["intro"],
                      "layout": "section", "section_key": key, "body_md": ""})
    return pages


def by_date(pages):
    return sorted(pages, key=lambda p: (str(p.get("updated", "")), -p.get("order", 99)), reverse=True)


def home_html(meta, articles):
    guias = sorted([p for p in articles if p["section"] == "guias"], key=lambda p: p.get("order", 99))
    resenas = by_date([p for p in articles if p["section"] == "resenas"])
    blog = by_date([p for p in articles if p["section"] == "blog"])
    mios = [p for p in PRODUCTOS if p.get("propio") and not p.get("etiqueta")]
    ig = CFG.get("instagram", "")
    ig_user = "@" + ig.rstrip("/").split("/")[-1] if ig else ""
    igband = (f'<section class="igband"><h2>Mi café, también en Instagram.</h2>'
              f'<p>Reseñas en un minuto, trucos y lo que voy probando.</p>'
              f'<a class="buy light" href="{ig}" rel="me noopener" target="_blank">Seguir a {ig_user}</a></section>') if ig else ""
    return f"""
<section class="hero">
  <div class="hero-text">
    <h1>{E(meta.get('hero', 'Buen café en casa, sin complicarte.'))}</h1>
    <p class="intro">{E(meta.get('intro', ''))}</p>
    <p class="hero-cta"><a class="buy" href="{link('guias')}">Ver las guías de compra</a>
    <a class="ghost" href="{link('resenas/cecotec-power-espresso-20')}">La cafetera que uso</a></p>
  </div>
  <div class="hero-art cat-espresso">{icon('espresso')}</div>
</section>

<section class="band">
  <div class="band-head"><h2>Lo que uso cada día.</h2><a class="more" href="{link('productos')}">Ver todos los productos</a></div>
  <ul class="pgrid">{''.join(card(p) for p in mios)}</ul>
</section>

<section class="band">
  <div class="band-head"><h2>Guías de compra.</h2><a class="more" href="{link('guias')}">Ver todas las guías</a></div>
  {guide_feature(guias, 7)}
</section>

<section class="trust">
  <h2>Por qué fiarte de lo que lees aquí.</h2>
  <ul>
    <li><strong>Lo uso de verdad.</strong><span>Cuando un producto lo tengo en casa, lo verás marcado. Mi cafetera, mi molinillo y mi café de cada día están aquí.</span></li>
    <li><strong>Te cuento lo malo.</strong><span>El ruido, el goteo, lo que no me convenció. Si algo tiene defectos, los vas a leer antes de comprar.</span></li>
    <li><strong>Ninguna marca me paga.</strong><span>Si compras desde mis enlaces, Amazon me da una pequeña comisión. Las opiniones son mías.</span></li>
  </ul>
</section>

<section class="founder">
  <div class="founder-art cat-cafe">{icon('cafe')}</div>
  <div class="founder-text">
    <h2>Hola, soy Eric.</h2>
    <p>En casa somos dos y el café con leche de la mañana es sagrado. He pasado por tres cafeteras de brazo, he cambiado el café de paquete por grano recién molido y he probado unos cuantos cafés por el camino.</p>
    <p>Esta web es lo que me habría gustado encontrar al empezar: pocas recomendaciones, explicadas con calma y con lo bueno y lo malo de cada cosa.</p>
    <p class="hero-cta"><a class="ghost" href="{link('sobre-mi')}">Conóceme un poco más</a></p>
  </div>
</section>

<section class="band">
  <div class="band-head"><h2>Reseñas.</h2><a class="more" href="{link('resenas')}">Ver todas las reseñas</a></div>
  {review_rows(resenas, 3)}
</section>

<section class="band">
  <div class="band-head"><h2>Del blog.</h2><a class="more" href="{link('blog')}">Ver todo el blog</a></div>
  {story_rows(blog, 3)}
</section>

{igband}
"""


def page_html(meta, content, articles=()):
    slug = meta["slug"]
    title = meta["title"] if slug == "" else f"{meta['title']} | {CFG['title']}"
    desc = meta.get("description", CFG["description"])
    canonical = CFG["url"] + CFG["baseurl"].rstrip("/") + "/" + (slug + "/" if slug else "")
    is_article = meta.get("layout") == "article"
    current = meta.get("section") or meta.get("section_key") or slug.split("/")[0]
    jsonld = ""
    if is_article:
        data = {"@context": "https://schema.org", "@type": "Article",
                "headline": meta["title"], "description": desc,
                "author": {"@type": "Person", "name": CFG["author"]},
                "dateModified": str(meta.get("updated", dt.date.today())),
                "publisher": {"@type": "Organization", "name": CFG["title"], "url": CFG["url"], "sameAs": [CFG["instagram"]] if CFG.get("instagram") else []},
                "mainEntityOfPage": canonical, "inLanguage": CFG["lang"]}
        prod = BYID.get(meta.get("producto"))
        if meta["section"] == "resenas" and prod and prod.get("propio"):
            # Solo los productos que el autor usa de verdad se marcan como reseña para Google:
            # un Product con su Review dentro (Google exige offers, review o aggregateRating).
            def notes(items):
                return {"@type": "ItemList", "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": t} for i, t in enumerate(items)]}
            review = {"@type": "Review",
                      "author": {"@type": "Person", "name": CFG["author"],
                                 "url": CFG["url"] + CFG["baseurl"].rstrip("/") + "/sobre-mi/"},
                      "datePublished": str(meta.get("updated", dt.date.today())),
                      "name": meta["title"], "reviewBody": meta.get("veredicto", ""),
                      "inLanguage": CFG["lang"]}
            if meta.get("pros"):
                review["positiveNotes"] = notes(meta["pros"])
            if meta.get("contras"):
                review["negativeNotes"] = notes(meta["contras"])
            if meta.get("nota"):
                review["reviewRating"] = {"@type": "Rating", "ratingValue": meta["nota"],
                                          "bestRating": 5, "worstRating": 1}
            data = {"@context": "https://schema.org", "@type": "Product", "name": prod["nombre"],
                    "brand": {"@type": "Brand", "name": prod.get("marca", "")}, "review": review}
            if prod.get("asin"):
                data["sku"] = prod["asin"]
        jsonld = f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'

    cur_attr = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{link(k)}"{cur_attr if current == k else ""}>{label}</a></li>'
        for k, label in NAV)

    av = CFG.get("aviso") or {}
    aviso = (f'<p class="aviso">{E(av.get("texto", ""))} <a href="{link(av.get("enlace", ""))}">{E(av.get("boton", "Leer"))}</a></p>'
             if av.get("texto") else "")
    ig_link = (f'<li class="ig"><a href="{CFG["instagram"]}" rel="me noopener" target="_blank" aria-label="Instagram">'
               '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/>'
               '<circle cx="12" cy="12" r="4.2"/><circle cx="17.3" cy="6.7" r="1.1"/></svg></a></li>') if CFG.get("instagram") else ""

    if is_article:
        sec = SECTIONS[meta["section"]]
        upd = meta.get("updated")
        toc = "".join(f'<li><a href="#{a}">{re.sub("<[^>]+>", "", t)}</a></li>'
                      for a, t in re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', content))
        ig = CFG.get("instagram", "")
        aside = f"""
    <aside class="article-aside" aria-label="En esta página">
      <div class="aside-sticky">
        {f'<p class="aside-title">En esta página</p><ul class="toc">{toc}</ul>' if toc else ''}
        <div class="aside-card">
          <p><strong>Escrito por {E(CFG['author'])}</strong>, que prepara su café cada mañana con una cafetera de brazo y grano recién molido.</p>
          <p><a href="{link('sobre-mi')}">Sobre mí</a>{f' · <a href="{ig}" rel="me noopener" target="_blank">Instagram</a>' if ig else ''}</p>
        </div>
      </div>
    </aside>"""
        main = f"""
<article class="article">
  <header class="article-head">
    <p class="crumbs"><a href="{link('')}">Inicio</a> / <a href="{link(meta['section'])}">{sec['title']}</a></p>
    <h1>{E(meta['title'])}</h1>
    <p class="lede">{E(meta.get('lede', desc))}</p>
    <p class="byline">Por <a href="{link('sobre-mi')}">{E(CFG['author'])}</a>. Actualizado el {fecha_es(upd)}.</p>
  </header>
  {review_box(meta) if meta['section'] == 'resenas' else ''}
  <div class="article-grid">
    <div class="prose">
      <p class="disclosure">Los enlaces a Amazon de esta página son de afiliado: si compras a través de ellos, recibo una pequeña comisión sin que a ti te cueste más. <a href="{link('afiliados')}">Cómo elijo los productos</a>.</p>
      {content}
      {f'<p class="pricenote">{E(PRICE_NOTE)}</p>' if PRICE_NOTE and ('prange real' in content or meta['section'] == 'resenas') else ''}
    </div>{aside}
  </div>
</article>"""
    elif slug == "":
        main = home_html(meta, articles)
    elif meta.get("layout") == "section":
        main = f'<header class="section-head"><h1>{E(meta["title"])}</h1><p class="lede">{E(meta["description"])}</p></header>{content}'
    else:
        if meta.get("arte"):
            main = (f'<div class="page-split"><div class="prose page">{content}</div>'
                    f'<div class="page-art cat-{meta["arte"]}">{icon(meta["arte"])}</div></div>')
        else:
            main = f'<div class="{"wide" if meta.get("wide") else "prose"} page {meta.get("class", "")}">{content}</div>'

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#2E241F">
<script>try{{if(localStorage.getItem("tema")==="light")document.documentElement.dataset.theme="light"}}catch(e){{}}</script>
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{'article' if is_article else 'website'}">
<meta property="og:title" content="{E(meta['title'])}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{CFG['title']}">
<meta property="og:locale" content="es_ES">
<meta property="og:image" content="{CFG['url']}{CFG['baseurl'].rstrip('/')}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Grano y Taza: guías y reseñas reales para hacer buen café en casa">
<meta name="twitter:card" content="summary_large_image">
{'<meta name="robots" content="noindex">' if meta.get('noindex') else ''}
<link rel="icon" href="{BASE}/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Young+Serif&family=Public+Sans:ital,wght@0,400;0,600;0,700;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{BASE}/style.css">
{jsonld}
</head>
<body>
<a class="skip" href="#contenido">Saltar al contenido</a>
{aviso}
<header class="site-head">
  <a class="brand" href="{link('')}"><svg viewBox="0 0 32 32" aria-hidden="true"><ellipse cx="16" cy="16" rx="10" ry="13" transform="rotate(30 16 16)"/><path d="M11 6c6 6-2 14 4 20"/></svg>{CFG['title']}</a>
  <nav aria-label="Apartados"><ul>{nav}{ig_link}<li><button class="theme-toggle" type="button" aria-label="Cambiar a modo claro" title="Modo claro / oscuro"><svg class="moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/></svg><svg class="sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button></li></ul></nav>
</header>
<main id="contenido">{main}</main>
<footer class="site-foot">
  <p class="foot-disclosure">{DISCLOSURE}</p>
  <ul>
    <li><a href="{link('sobre-mi')}">Sobre mí</a></li>
    <li><a href="{link('afiliados')}">Afiliados y método</a></li>
    <li><a href="{link('aviso-legal')}">Aviso legal</a></li>
    <li><a href="{link('privacidad')}">Privacidad</a></li>
    <li><a href="{link('cookies')}">Cookies</a></li>
    {f'<li><a href="{CFG["instagram"]}" rel="me noopener" target="_blank">Instagram</a></li>' if CFG.get("instagram") else ''}
  </ul>
  <p>© {dt.date.today().year} {CFG['title']}</p>
</footer>
<script>(function(){{var b=document.querySelector(".theme-toggle");if(!b)return;var r=document.documentElement;
function lbl(){{b.setAttribute("aria-label",r.dataset.theme==="light"?"Cambiar a modo oscuro":"Cambiar a modo claro")}}lbl();
b.addEventListener("click",function(){{r.classList.add("theme-anim");b.classList.add("spin");setTimeout(function(){{b.classList.remove("spin")}},180);clearTimeout(window._ta);window._ta=setTimeout(function(){{r.classList.remove("theme-anim")}},400);var l=r.dataset.theme!=="light";if(l)r.dataset.theme="light";else delete r.dataset.theme;
try{{localStorage.setItem("tema",l?"light":"dark")}}catch(e){{}}lbl()}})}})();</script>
</body>
</html>"""


def relativize(htmltext, depth):
    """Para la vista previa: enlaces absolutos -> relativos y carpetas -> index.html."""
    prefix = "../" * depth if depth else "./"

    def fix(m):
        attr, path = m.group(1), m.group(2)
        path, q = (path.split("?", 1) + [""])[:2]
        if path.endswith("/") or path == "":
            path += "index.html"
        return f'{attr}="{prefix}{path.lstrip("/")}{"?" + q if q else ""}"'
    return re.sub(r'(href|src)="/(?!/)([^"]*)"', fix, htmltext)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    pages = load_pages()
    articles = [p for p in pages if p.get("layout") == "article"]
    for meta in pages:
        body = meta["body_md"]
        content = render_body(body) if body.strip() else ""
        if meta.get("layout") == "section":
            key = meta["section_key"]
            items = [p for p in articles if p["section"] == key]
            items = sorted(items, key=lambda p: p.get("order", 99)) if key == "guias" else by_date(items)
            content = (story_rows(items) if key == 'blog' else review_rows(items) if key == 'resenas' else guide_feature(items)) if items else '<p class="empty">Todavía no hay entradas en este apartado.</p>'
        repl = {
            "{{CATALOGO}}": catalog_html,
            "{{DESTACADOS}}": lambda: '<ul class="pgrid featured">' + "".join(
                card(p) for p in sorted(PRODUCTOS, key=lambda p: -p.get("relevancia", 0))[:4]) + "</ul>",
            "{{GUIAS}}": lambda: entry_list(sorted([p for p in articles if p["section"] == "guias"],
                                                   key=lambda p: p.get("order", 99)), compact=True),
            "{{RESENAS}}": lambda: entry_list(by_date([p for p in articles if p["section"] == "resenas"])[:3], compact=True),
            "{{BLOG}}": lambda: entry_list(by_date([p for p in articles if p["section"] == "blog"])[:3], compact=True),
        }
        for k, fn in repl.items():
            if k in content:
                content = re.sub(rf"<p>\s*{re.escape(k)}\s*</p>", lambda _m: fn(), content)
                content = content.replace(k, fn()) if k in content else content
        slug = meta["slug"]
        dest = OUT / "404.html" if slug == "404" else (OUT / slug / "index.html" if slug else OUT / "index.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        out = page_html(meta, content, articles)
        if PREVIEW:
            depth = len(dest.relative_to(OUT).parts) - 1
            css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
            out = out.replace(f'<link rel="stylesheet" href="{BASE}/style.css">', f"<style>{css}</style>")
            out = relativize(out, depth)
        dest.write_text(out, encoding="utf-8")

    if not PREVIEW:
        root = CFG["url"] + CFG["baseurl"].rstrip("/")
        urls = [root + "/" + (p["slug"] + "/" if p["slug"] else "") for p in pages
                if not p.get("noindex")]
        (OUT / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
        (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {root}/sitemap.xml\n")
        (OUT / ".nojekyll").write_text("")
    print(f"OK: {len(pages)} páginas en {OUT}")


if __name__ == "__main__":
    main()
