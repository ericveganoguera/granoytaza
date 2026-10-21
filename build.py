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

ROOT = Path(__file__).parent
PREVIEW = "--preview" in sys.argv
OUT = ROOT / ("_preview" if PREVIEW else "_site")
CFG = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
CAT = yaml.safe_load((ROOT / "data" / "productos.yaml").read_text(encoding="utf-8"))
CATEGORIAS = CAT["categorias"]
PRODUCTOS = CAT["productos"]
BYID = {p["id"]: p for p in PRODUCTOS}
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
    "molinillo": "molinillo cafe", "italiana": "cafetera italiana",
    "filtro": "cafetera filtro manual", "accesorio": "accesorios cafe barista",
}
RANGOS = [(0, 50, "Menos de 50 €"), (50, 150, "50–150 €"), (150, 300, "150–300 €"),
          (300, 600, "300–600 €"), (600, 1000, "600–1.000 €"), (1000, 10**6, "Más de 1.000 €")]

ICONS = {  # ilustraciones de línea por categoría (no se usan fotos de Amazon sin su API)
    "espresso": '<rect x="30" y="14" width="60" height="16" rx="3"/><rect x="34" y="30" width="52" height="40"/><path d="M44 38h24v6H44z"/><path d="M52 44v8m8-8v8"/><path d="M50 58h20v8a6 6 0 0 1-6 6h-8a6 6 0 0 1-6-6z"/><path d="M70 61h4a3 3 0 0 1 0 6h-4"/><path d="M24 76h72"/>',
    "superautomatica": '<rect x="28" y="12" width="64" height="62" rx="6"/><rect x="38" y="20" width="26" height="12" rx="2"/><circle cx="76" cy="26" r="4"/><path d="M54 40v10m10-10v10"/><path d="M50 56h22v8a6 6 0 0 1-6 6h-10a6 6 0 0 1-6-6z"/><path d="M22 78h76"/>',
    "molinillo": '<path d="M44 10h32l-6 20H50z"/><rect x="40" y="30" width="40" height="36" rx="4"/><circle cx="60" cy="48" r="7"/><path d="M48 66h24v10H48z"/><path d="M34 80h52"/>',
    "italiana": '<path d="M42 12h34l-6 26H48z"/><path d="M46 38h26"/><path d="M48 38l-6 34h34l-6-34"/><path d="M76 18c10 2 10 18 0 22"/><path d="M58 8v4"/><path d="M34 76h52"/>',
    "filtro": '<path d="M36 18h48L68 46H52z"/><path d="M44 46h32"/><path d="M42 50h36l-4 24H46z"/><path d="M60 10v4m-8-2v4m16-4v4"/><path d="M34 78h52"/>',
    "accesorio": '<rect x="26" y="50" width="68" height="20" rx="4"/><rect x="48" y="56" width="24" height="8" rx="2"/><path d="M44 50c0-14 32-14 32 0"/><path d="M60 20c-6 6 6 10 0 16"/><path d="M22 76h76"/>',
}


def icon(cat):
    return (f'<svg viewBox="0 0 120 90" aria-hidden="true" fill="none" stroke="currentColor" '
            f'stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{ICONS.get(cat, ICONS["accesorio"])}</svg>')


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
    if p.get("id") in BYID:
        p = {**BYID[p["id"]], **p}
    gama = p.get("gama", "media")
    pros = "".join(f"<li>{E(x)}</li>" for x in p.get("pros", []))
    cons = "".join(f"<li>{E(x)}</li>" for x in p.get("contras", []))
    review = (f' <a class="more" href="{link(p["resena"])}">Leer la reseña completa</a>'
              if p.get("resena") else "")
    return f"""
<section class="product" data-gama="{gama}">
  <header class="product-head">
    <p class="gama"><span class="roast roast-{gama}" aria-hidden="true"></span>{GAMAS.get(gama, gama)}</p>
    <h3>{E(p['nombre'])}</h3>
    <p class="ideal">Ideal para: {E(p.get('ideal', ''))}</p>
  </header>
  <div class="product-body">{md(p.get('texto', ''))}</div>
  <div class="procon">
    <div><h4>Lo mejor</h4><ul class="pros">{pros}</ul></div>
    <div><h4>A tener en cuenta</h4><ul class="cons">{cons}</ul></div>
  </div>
  <p class="actions"><a class="buy" href="{E(prod_url(p))}" {SPONSORED}>Ver precio en Amazon</a>{review}</p>
</section>
"""


def card(p, heading="h3"):
    extra = ""
    if p.get("resena"):
        extra = f'<a class="more" href="{link(p["resena"])}">Leer reseña</a>'
    elif p.get("guia"):
        extra = f'<a class="more" href="{link(p["guia"])}">Ver en la guía</a>'
    gama = p.get("gama", "media")
    return f"""<li class="pcard" data-cat="{p['categoria']}" data-gama="{gama}" data-precio="{p['precio']}"
 data-rel="{p.get('relevancia', 50)}" data-fecha="{p.get('anadido', '')}" data-marca="{E(p.get('marca', ''))}"
 data-texto="{E((p['nombre'] + ' ' + p.get('marca', '') + ' ' + p.get('resumen', '')).lower())}">
  <div class="pimg cat-{p['categoria']}">{icon(p['categoria'])}</div>
  <p class="pcat">{E(CATEGORIAS.get(p['categoria'], ''))}</p>
  <{heading} class="pname">{E(p['nombre'])}</{heading}>
  <p class="psum">{E(p.get('resumen', ''))}</p>
  <p class="pmeta"><span class="roast roast-{gama}" aria-hidden="true"></span><span>{GAMAS[gama]}</span><span class="prange">{rango(p['precio'])}</span></p>
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


def review_box(meta):
    p = BYID.get(meta.get("producto"))
    if not p:
        return ""
    pros = "".join(f"<li>{E(x)}</li>" for x in meta.get("pros", []))
    cons = "".join(f"<li>{E(x)}</li>" for x in meta.get("contras", []))
    datos = "".join(f"<tr><th>{E(k)}</th><td>{E(str(v))}</td></tr>" for k, v in (meta.get("ficha") or {}).items())
    return f"""
<aside class="verdict" aria-label="Resumen de la reseña">
  <div class="vimg cat-{p['categoria']}">{icon(p['categoria'])}</div>
  <div class="vbody">
    <p class="gama"><span class="roast roast-{p['gama']}" aria-hidden="true"></span>{GAMAS[p['gama']]}<span class="prange">{rango(p['precio'])}</span></p>
    <h2>Veredicto</h2>
    <p>{E(meta.get('veredicto', ''))}</p>
    <div class="procon"><div><h4>Lo mejor</h4><ul class="pros">{pros}</ul></div>
    <div><h4>A tener en cuenta</h4><ul class="cons">{cons}</ul></div></div>
    {f'<table class="ficha">{datos}</table>' if datos else ''}
    <p class="actions"><a class="buy" href="{E(prod_url(p))}" {SPONSORED}>Ver precio en Amazon</a></p>
  </div>
</aside>"""


# ---------- render ----------

def render_body(text):
    text = text.replace("{{base}}", BASE)
    parts, last = [], 0
    for m in re.finditer(r"^::: producto\n(.*?)\n:::\s*$", text, flags=re.S | re.M):
        parts.append(md(text[last:m.start()]))
        parts.append(render_product(m.group(1)))
        last = m.end()
    parts.append(md(text[last:]))
    out = "".join(parts)

    def fix(m):
        kind, val = m.group(1), html.unescape(m.group(2))
        if kind == "catalogo":
            return f'<a href="{link("productos")}?cat={E(val)}"'
        url = amazon_url(asin=val) if kind == "amazon-dp" else amazon_url(val)
        return f'<a href="{E(url)}" {SPONSORED}'
    return re.sub(r'<a href="(amazon|amazon-dp|catalogo):([^"]+)"', fix, out)


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


def page_html(meta, content):
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
                "publisher": {"@type": "Organization", "name": CFG["title"]},
                "mainEntityOfPage": canonical, "inLanguage": CFG["lang"]}
        if meta["section"] == "resenas" and meta.get("producto") in BYID:
            data = {"@context": "https://schema.org", "@type": "Review", "name": meta["title"],
                    "author": {"@type": "Person", "name": CFG["author"]},
                    "itemReviewed": {"@type": "Product", "name": BYID[meta["producto"]]["nombre"],
                                     "brand": BYID[meta["producto"]].get("marca", "")},
                    "reviewBody": meta.get("veredicto", ""), "inLanguage": CFG["lang"]}
        jsonld = f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>'

    cur_attr = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{link(k)}"{cur_attr if current == k else ""}>{label}</a></li>'
        for k, label in NAV)

    if is_article:
        sec = SECTIONS[meta["section"]]
        upd = meta.get("updated")
        main = f"""
<article class="article">
  <header class="article-head">
    <p class="crumbs"><a href="{link('')}">Inicio</a> / <a href="{link(meta['section'])}">{sec['title']}</a></p>
    <h1>{E(meta['title'])}</h1>
    <p class="lede">{E(meta.get('lede', desc))}</p>
    <p class="byline">Por <a href="{link('sobre-mi')}">{E(CFG['author'])}</a>. Actualizado el {fecha_es(upd)}.</p>
    <p class="disclosure">Los enlaces a Amazon de esta página son de afiliado: si compras a través de ellos, recibo una pequeña comisión sin que a ti te cueste más. <a href="{link('afiliados')}">Cómo elijo los productos</a>.</p>
  </header>
  {review_box(meta) if meta['section'] == 'resenas' else ''}
  <div class="prose">{content}</div>
</article>"""
    elif meta.get("layout") == "section":
        main = f'<header class="section-head"><h1>{E(meta["title"])}</h1><p class="lede">{E(meta["description"])}</p></header>{content}'
    else:
        main = f'<div class="{"wide" if meta.get("wide") else "prose"} page {meta.get("class", "")}">{content}</div>'

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{'article' if is_article else 'website'}">
<meta property="og:title" content="{E(meta['title'])}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="{CFG['title']}">
<meta property="og:locale" content="es_ES">
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
<div class="roastbar" aria-hidden="true"></div>
<header class="site-head">
  <a class="brand" href="{link('')}"><svg viewBox="0 0 32 32" aria-hidden="true"><ellipse cx="16" cy="16" rx="10" ry="13" transform="rotate(30 16 16)"/><path d="M11 6c6 6-2 14 4 20"/></svg>{CFG['title']}</a>
  <nav aria-label="Apartados"><ul>{nav}</ul></nav>
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
  </ul>
  <p>© {dt.date.today().year} {CFG['title']}</p>
</footer>
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
            content = entry_list(items) if items else '<p class="empty">Todavía no hay entradas en este apartado.</p>'
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
        out = page_html(meta, content)
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
