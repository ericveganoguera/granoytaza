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
---
```

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

## Precios e imágenes reales

Amazon solo permite mostrar precios e imágenes obtenidos de su API (Creators API), que exige
10 ventas cualificadas en 30 días. Cuando la tengas, se puede añadir una tarea automática que
actualice `data/productos.yaml` cada día con precio, imagen y valoración.
