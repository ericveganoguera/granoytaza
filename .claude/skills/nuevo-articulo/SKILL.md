---
name: nuevo-articulo
description: Crea una guía de compra, reseña o entrada de blog nueva para granoytaza.es con la cabecera, las fichas de producto y los enlaces internos correctos. Úsala cuando haya que escribir un artículo nuevo.
disable-model-invocation: true
argument-hint: "[guia|resena|blog] tema del artículo"
---

# Nuevo artículo para Grano y Taza

Petición: $ARGUMENTS

## 0. Transparencia antes que nada

- No inventes datos: ni precios, ni especificaciones, ni fechas, ni ASIN, ni opiniones de
  compradores, ni experiencias de Eric. Si un dato no lo encuentras en una fuente fiable,
  no lo pongas y dilo al terminar.
- Lo que solo puede aportar Eric (su experiencia, sus fotos, su nota) va como marcador:
  `<!-- AÑADE AQUÍ TU EXPERIENCIA: qué contar exactamente -->` o `<!-- FOTO: qué foto -->`.
- Al acabar, lista qué datos has comprobado (con la fuente), cuáles no has podido comprobar
  y qué marcadores ha de rellenar Eric.

## 1. Antes de escribir

1. Lee 2 artículos del mismo apartado para copiar el tono y la estructura:
   - Guía: `content/guias/mejores-cafeteras-espresso.md`
   - Reseña: `content/resenas/cecotec-power-espresso-20.md`
   - Blog: `content/blog/como-usar-cafetera-italiana.md`
2. Comprueba que no exista ya un artículo sobre lo mismo (`ls content/*/` y grep del tema).
   Si existe, propón mejorar ese en vez de crear otro (dos páginas iguales compiten en Google).
3. Mira en `data/productos.yaml` qué productos del catálogo encajan. Si falta alguno, usa
   `/anadir-producto` primero.

## 2. Archivo y cabecera

Ruta: `content/guias/<slug>.md`, `content/resenas/<slug>.md` o `content/blog/<slug>.md`.
El slug en minúsculas, sin tildes y con guiones (será la URL).

```yaml
---
title: "Título completo para la página (con el año si es una guía)"
seo_title: "Título corto para Google (máx. ~55 caracteres)"
description: "Meta descripción de 140-160 caracteres con la búsqueda principal."
lede: "Entradilla de una o dos frases bajo el título."
summary: "Una frase para las tarjetas del listado."
updated: AAAA-MM-DD   # fecha de hoy
# Solo guías:
order: N              # posición en la lista de guías
nav: "Nombre corto"   # opcional
# Solo reseñas (ver README, "Escribir una reseña"):
producto: id-del-catalogo
veredicto: "..."
pros: ["..."]
contras: ["..."]
ficha:
  Tipo: "..."
nota: N               # SOLO si Eric da su nota; si no, no pongas este campo
---
```

Una reseña solo se escribe de un producto con `propio: true` (que Eric usa). Si no lo usa,
es una guía o comparativa, no una reseña.

## 3. Cuerpo

- Guías: empieza con `## Respuesta rápida` (tabla "Si buscas… | Mi elección"), luego criterios
  para elegir, luego las fichas por presupuesto.
- Productos: fichas con `::: producto` (con `id:` del catálogo) o rejilla con `::: productos`.
- Enlaces a Amazon: solo con `amazon-dp:ASIN` (preferido) o `amazon:Texto+de+busqueda`.
  Nunca una URL de Amazon pegada a mano ni un precio exacto escrito a mano.
- Enlaces internos con `{{base}}/guias/slug/`: al menos 2 a guías o posts relacionados, y
  añade un enlace hacia el nuevo artículo desde 1 o 2 artículos que ya existan.
- Si el producto es de Eric, deja marcadores para su experiencia y sus fotos.

## 4. Comprobar

1. `python3 build.py --preview` tiene que terminar en `OK` y sin líneas `AVISO`
   (el hook lo hace solo tras cada edición).
2. Pasa el artículo por los subagentes `revisor-afiliados` y `revisor-seo` y corrige lo que digan.
3. Resume: archivo creado, enlaces internos añadidos, datos no verificados y marcadores pendientes.
