# Grano y Taza

Web de guías de compra de café para casa, monetizada con Amazon Afiliados.
Se publica sola en GitHub Pages cada vez que se sube un cambio a `main`.

## Estructura

| Apartado | Carpeta | URL |
|---|---|---|
| Guías de compra | `content/guias/` | `/guias/...` |
| Reseñas | `content/resenas/` | `/resenas/...` |
| Blog | `content/blog/` | `/blog/...` |
| Productos (cuadrícula con filtros) | `data/productos.yaml` | `/productos/` |

Cada `.md` dentro de esas carpetas es un artículo; su portada de apartado se genera sola.
Otras páginas: `content/index.md` (portada), `sobre-mi`, `afiliados`, `aviso-legal`, `privacidad`, `cookies`.

- `site.yaml` — ID de afiliado, nombre, URL y email.
- `static/` — estilos, icono e imágenes.
- `build.py` — genera la web (no hace falta tocarlo).

## Añadir un producto al catálogo

Añade un bloque en `data/productos.yaml` (mira los existentes). Campos clave:
`categoria`, `gama` (basica/media/alta), `precio` (aproximado, solo para filtrar y ordenar),
`relevancia` (1-100), `anadido` (fecha, para "Novedades"), `buscar` o `asin`, y opcionalmente `resena` o `guia`.

## Fotos de producto

Por contrato, las fotos de Amazon solo pueden mostrarse si vienen de su API (se activan solas
cuando la cuenta tenga acceso). Mientras tanto se muestra una ilustración por categoría.
Para usar una foto tuya: súbela a `static/img/` y añade `foto: img/archivo.jpg` al producto
en `data/productos.yaml`. La imagen, el nombre y el botón llevan siempre a Amazon con tu ID.

## Rejilla de productos dentro de un artículo

```
::: productos
- id: dedica-ec685
  nota: "Texto corto de por qué lo recomiendas (opcional)"
- magnifica-s
:::
```

Cualquier enlace con el texto `Ver en Amazon` se muestra como botón.

## Escribir una reseña

Crea `content/resenas/nombre.md` con esta cabecera:

```
---
title: "..."
description: "..."
lede: "..."
summary: "..."
producto: id-del-catalogo
updated: 2026-10-21
veredicto: "..."
pros: ["...", "..."]
contras: ["...", "..."]
ficha:
  Tipo: "..."
nota: 4        # tu puntuación de 1 a 5 (opcional)
---
```

Si el producto tiene `propio: true` en el catálogo (lo usas de verdad), la reseña se marca
para Google como reseña de producto (con tu nota y tus pros y contras). Si no, como artículo.

## Enlaces especiales en el texto

```
[texto](amazon:DeLonghi+Dedica+EC685)   -> búsqueda en Amazon con tu ID
[texto](amazon-dp:B0XXXXXXXX)           -> ficha concreta por ASIN
[texto](catalogo:molinillo)             -> cuadrícula filtrada por categoría
```

La cuadrícula también acepta filtros por URL: `/productos/?cat=molinillo&precio=50-150&orden=precio-asc`.

## Ficha de producto dentro de una guía

```
::: producto
id: dedica-ec685          (opcional: toma datos del catálogo)
nombre: ...
gama: basica | media | alta
ideal: para quién es
texto: "Análisis en un párrafo."
pros: ["...", "..."]
contras: ["...", "..."]
:::
```

## Probar en local

```
pip install markdown pyyaml
python3 build.py             # web final en _site/
python3 build.py --preview   # vista previa con enlaces relativos en _preview/
```

## Precios e imágenes reales (API de Amazon)

La web se conecta sola a la Creators API de Amazon dos veces al día (`scripts/amazon_api.py`).
Requisito de Amazon: al menos 10 ventas cualificadas en los últimos 30 días.

1. En afiliados.amazon.es: Herramientas → Creators API → Crear aplicación → Añadir credencial.
   Apunta el Credential ID, el Secret (solo se muestra una vez) y la versión.
2. En GitHub: Settings → Secrets and variables → Actions → New repository secret, y crea
   `AMAZON_CREDENTIAL_ID`, `AMAZON_CREDENTIAL_SECRET` y `AMAZON_CREDENTIAL_VERSION`.
3. Actions → "Comprobar acceso a la API de Amazon" → Run workflow. El resumen dice si funciona.

Con acceso, cada tarjeta, ficha y reseña muestra foto, precio exacto y la hora del precio.
Sin acceso (o si la API falla), la web se publica igual con los rangos de precio.

Los productos sin `asin` se buscan por su texto `buscar`; el registro de la ejecución
lista los ASIN encontrados para que los copies en `data/productos.yaml` y queden fijados.
