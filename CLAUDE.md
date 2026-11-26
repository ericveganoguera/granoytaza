# Grano y Taza (granoytaza.es)

Web de guías de compra de café para casa, en español, monetizada con Amazon Afiliados
(tag `granoytaza-21`). Autor: Eric. Todo lo que se fusiona a `main` se publica solo en
GitHub Pages, así que fusionar es publicar.

## Regla número uno: transparencia

- **Nunca te inventes nada.** Ni precios, ni especificaciones, ni fechas, ni cifras, ni
  fuentes, ni experiencias de uso, ni opiniones de compradores, ni resultados de comandos.
- **Si no lo sabes o no lo encuentras, dilo siempre**, claramente y en el momento. Es mejor
  un hueco marcado que un dato inventado.
- Distingue siempre lo que has **comprobado** (y cómo) de lo que **supones**. Si algo es una
  estimación, escríbelo como estimación.
- En el contenido, lo que solo Eric puede aportar (su experiencia, sus fotos, su nota) se
  deja como marcador `<!-- AÑADE AQUÍ TU EXPERIENCIA: ... -->` o `<!-- FOTO: ... -->`, nunca
  se rellena con algo inventado.
- Si una tarea no ha salido como se pedía (un build falla, un dato no se pudo verificar, un
  paso se ha saltado), dilo tal cual.

## Cómo está hecha

- `build.py`: generador estático en Python (markdown + pyyaml). No hay framework.
  - `python3 build.py --preview` genera `_preview/` (enlaces relativos, para revisar).
  - `python3 build.py` genera `_site/` (lo que se publica).
  - Dependencias: `pip install markdown pyyaml`.
- `content/guias/`, `content/resenas/`, `content/blog/`: cada `.md` es una página.
- `data/productos.yaml`: catálogo de productos (alimenta `/productos/`, tarjetas y fichas).
- `site.yaml`: tag de afiliado, dominio, textos generales y la barra de aviso superior.
- `static/`: CSS, JS e imágenes (`static/img/`). `static/CNAME` es el dominio: no tocar.
- `scripts/amazon_api.py`: precios e imágenes de la Creators API de Amazon. Escribe
  `data/amazon.json`, que es generado y no se versiona.
- `.github/workflows/pages.yml`: publica en cada push a `main` y dos veces al día.

La sintaxis especial de los `.md` (`amazon:`, `amazon-dp:`, `catalogo:`, `::: producto`,
`::: productos`, `{{base}}`) está explicada en el `README.md`.

## Normas de Amazon Afiliados (obligatorias)

- **No escribir precios exactos a mano.** Solo rangos (los pone el build) o precios de la API.
- Todo enlace a Amazon lleva el tag y `rel="sponsored"`: usa siempre `amazon:`/`amazon-dp:`
  o los componentes del build, nunca una URL de Amazon pegada a mano.
- No usar fotos de Amazon salvo las que vienen de la API. Fotos propias en `static/img/`.
- Mejor `amazon-dp:ASIN` que `amazon:búsqueda` cuando se conoce el ASIN (y el ASIN tiene que
  ser real y comprobado, no supuesto).
- Solo se marca como reseña de producto (`propio: true`) lo que Eric usa de verdad.

## Estilo del contenido

- Español de España, tuteando, sin jerga y pensando en el presupuesto del lector.
- Lo que mejor posiciona es lo de primera mano (comparativas de cosas que Eric ha tenido,
  reseñas de uso real). Las listas genéricas de productos no probados rinden poco.
- Fechas en `updated:` con formato `AAAA-MM-DD`.

## Automatizaciones de Claude Code en este repo

- Hooks (`.claude/settings.json`): instalan dependencias al empezar, compilan la vista previa
  tras cada edición de contenido y bloquean cambios en `static/CNAME`, el tag de afiliado y
  `data/amazon.json`.
- Skills: `/nuevo-articulo` y `/anadir-producto`.
- Subagentes: `revisor-afiliados` y `revisor-seo` (úsalos antes de abrir un PR de contenido).
