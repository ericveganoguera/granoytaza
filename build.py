#!/usr/bin/env python3
"""Generador estático de Grano y Taza.

Uso:  python3 build.py        -> genera la web en la carpeta _site/

Contenido en content/*.md con cabecera YAML. Sintaxis extra:
  [texto](amazon:Nombre+del+producto)   -> enlace de búsqueda en Amazon con tu ID
  [texto](amazon-dp:B0XXXXXXX)          -> enlace directo a una ficha (ASIN) con tu ID
  ::: producto
  nombre: ...
  buscar: Texto de búsqueda en Amazon   (o asin: B0XXXXXXX)
  gama: basica | media | alta
  ideal: Para quién es
  texto: Párrafo de análisis (admite markdown)
  pros: [..]
  contras: [..]
  :::
"""
import datetime as dt
import html
import json
import re
import shutil
import urllib.parse
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
CFG = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
BASE = CFG["baseurl"].rstrip("/")
GAMAS = {"basica": "Gama de entrada", "media": "Gama media", "alta": "Gama alta"}
DISCLOSURE = ("En calidad de Afiliado de Amazon, obtengo ingresos por las compras "
              "adscritas que cumplen los requisitos aplicables.")


def amazon_url(query=None, asin=None):
    d, tag = CFG["amazon_domain"], CFG["amazon_tag"]
    if asin:
        return f"https://{d}/dp/{asin}?tag={tag}"
    q = urllib.parse.quote_plus(query.replace("+", " "))
    return f"https://{d}/s?k={q}&tag={tag}"


def link(path):
    return f"{BASE}/{path.strip('/')}/" if path.strip("/") else f"{BASE}/"


def md(text):
    return markdown.markdown(text, extensions=["tables", "toc", "attr_list", "smarty"],
                             extension_configs={"toc": {"permalink": False},
                                                "smarty": {"smart_angled_quotes": True}})


def render_product(block):
    p = yaml.safe_load(block)
    url = amazon_url(asin=p.get("asin")) if p.get("asin") else amazon_url(p.get("buscar", p["nombre"]))
    gama = p.get("gama", "media")
    pros = "".join(f"<li>{html.escape(x)}</li>" for x in p.get("pros", []))
    cons = "".join(f"<li>{html.escape(x)}</li>" for x in p.get("contras", []))
    return f"""
<section class="product" data-gama="{gama}">
  <header class="product-head">
    <p class="gama"><span class="roast roast-{gama}" aria-hidden="true"></span>{GAMAS.get(gama, gama)}</p>
    <h3>{html.escape(p['nombre'])}</h3>
    <p class="ideal">Ideal para: {html.escape(p.get('ideal', ''))}</p>
  </header>
  <div class="product-body">{md(p.get('texto', ''))}</div>
  <div class="procon">
    <div><h4>Lo mejor</h4><ul class="pros">{pros}</ul></div>
    <div><h4>A tener en cuenta</h4><ul class="cons">{cons}</ul></div>
  </div>
  <a class="buy" href="{html.escape(url)}" rel="sponsored nofollow noopener" target="_blank">Ver precio en Amazon</a>
</section>
"""


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
        url = amazon_url(asin=val) if kind == "amazon-dp" else amazon_url(val)
        return f'<a href="{html.escape(url)}" rel="sponsored nofollow noopener" target="_blank"'
    return re.sub(r'<a href="(amazon|amazon-dp):([^"]+)"', fix, out)


def load_pages():
    pages = []
    for f in sorted((ROOT / "content").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        _, fm, body = raw.split("---", 2)
        meta = yaml.safe_load(fm)
        meta.setdefault("slug", "" if f.stem == "index" else f.stem)
        meta["body_md"] = body
        pages.append(meta)
    return pages


def page_html(meta, content, pages):
    title = meta["title"] if meta.get("slug") == "" else f"{meta['title']} | {CFG['title']}"
    desc = meta.get("description", CFG["description"])
    canonical = CFG["url"] + link(meta["slug"])
    is_article = meta.get("layout") == "article"
    jsonld = ""
    if is_article:
        jsonld = json.dumps({
            "@context": "https://schema.org", "@type": "Article",
            "headline": meta["title"], "description": desc,
            "author": {"@type": "Person", "name": CFG["author"],
                       "url": CFG["url"] + link("sobre-mi")},
            "dateModified": str(meta.get("updated", dt.date.today())),
            "publisher": {"@type": "Organization", "name": CFG["title"]},
            "mainEntityOfPage": canonical, "inLanguage": CFG["lang"],
        }, ensure_ascii=False)
        jsonld = f'<script type="application/ld+json">{jsonld}</script>'

    guides = [p for p in pages if p.get("layout") == "article"]
    nav = "".join(f'<li><a href="{link(p["slug"])}">{html.escape(p.get("nav", p["title"]))}</a></li>'
                  for p in sorted(guides, key=lambda p: p.get("order", 99)) if p.get("nav"))
    year = dt.date.today().year

    if is_article:
        upd = meta.get("updated")
        upd_txt = upd.strftime("%d/%m/%Y") if hasattr(upd, "strftime") else str(upd)
        main = f"""
<article class="article">
  <header class="article-head">
    <p class="crumbs"><a href="{link('')}">Inicio</a> / {html.escape(meta.get('section', 'Guías'))}</p>
    <h1>{html.escape(meta['title'])}</h1>
    <p class="lede">{html.escape(meta.get('lede', desc))}</p>
    <p class="byline">Por <a href="{link('sobre-mi')}">{html.escape(CFG['author'])}</a>. Actualizado el {upd_txt}.</p>
    <p class="disclosure">Los enlaces a Amazon de esta página son de afiliado: si compras a través de ellos, recibo una pequeña comisión sin que a ti te cueste más. <a href="{link('afiliados')}">Cómo elijo los productos</a>.</p>
  </header>
  <div class="prose">{content}</div>
</article>"""
    else:
        main = f'<div class="prose page {meta.get("class", "")}">{content}</div>'

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{'article' if is_article else 'website'}">
<meta property="og:title" content="{html.escape(meta['title'])}">
<meta property="og:description" content="{html.escape(desc)}">
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
<div class="roastbar" aria-hidden="true"></div>
<header class="site-head">
  <a class="brand" href="{link('')}"><svg viewBox="0 0 32 32" aria-hidden="true"><ellipse cx="16" cy="16" rx="10" ry="13" transform="rotate(30 16 16)"/><path d="M11 6c6 6-2 14 4 20"/></svg>{CFG['title']}</a>
  <nav aria-label="Guías"><ul>{nav}</ul></nav>
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
  <p>© {year} {CFG['title']}</p>
</footer>
</body>
</html>"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "static", OUT)
    pages = load_pages()
    for meta in pages:
        body = meta["body_md"]
        if meta.get("slug") == "":
            guides = sorted([p for p in pages if p.get("layout") == "article"],
                            key=lambda p: p.get("order", 99))
            cards = "".join(
                f'<li class="guide g-{p.get("kind", "guia")}"><a href="{link(p["slug"])}">'
                f'<span class="kind">{html.escape(p.get("kindlabel", "Guía de compra"))}</span>'
                f'<strong>{html.escape(p["title"])}</strong>'
                f'<span class="sum">{html.escape(p.get("summary", ""))}</span></a></li>'
                for p in guides)
            body = body.replace("{{GUIAS}}", f'<ul class="guides">{cards}</ul>')
        content = render_body(body)
        content = content.replace('<p><ul class="guides">', '<ul class="guides">')
        content = re.sub(r'(<ul class="guides">.*?</ul>)</p>', r"\1", content, flags=re.S)
        dest = OUT / meta["slug"] / "index.html" if meta["slug"] else OUT / "index.html"
        if meta["slug"] == "404":
            dest = OUT / "404.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page_html(meta, content, pages), encoding="utf-8")

    urls = [CFG["url"] + link(p["slug"]) for p in pages if not p.get("noindex")]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {CFG['url']}{BASE}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    print(f"OK: {len(pages)} páginas en {OUT}")


if __name__ == "__main__":
    main()
