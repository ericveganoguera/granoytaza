# Grano y Taza

Web de guías de compra de café para casa, monetizada con Amazon Afiliados.
Se publica sola en GitHub Pages cada vez que se sube un cambio a `main`.

## Dónde está cada cosa

- `site.yaml` — configuración: ID de afiliado, nombre, URL, email de contacto.
- `content/*.md` — cada archivo es una página. El nombre del archivo es la URL.
- `static/` — estilos, icono e imágenes.
- `build.py` — genera la web en `_site/` (no hace falta tocarlo).

## Añadir o editar un artículo

Se puede hacer desde la web de GitHub: abre `content/`, pulsa *Add file* o el lápiz de un archivo, guarda, y en uno o dos minutos está publicado.

Enlaces de afiliado dentro del texto:

```
[De'Longhi Dedica](amazon:DeLonghi+Dedica+EC685)   -> búsqueda en Amazon con tu ID
[De'Longhi Dedica](amazon-dp:B0XXXXXXXX)           -> ficha concreta por ASIN
```

Ficha de producto:

```
::: producto
nombre: Nombre del producto
buscar: Texto de búsqueda en Amazon     (o asin: B0XXXXXXXX)
gama: basica | media | alta
ideal: para quién es
texto: "Análisis en un párrafo."
pros: ["...", "..."]
contras: ["...", "..."]
:::
```

Los artículos de guía llevan `layout: article` en la cabecera; con `nav:` aparecen en el menú.

## Probar en local

```
pip install markdown pyyaml
python3 build.py
```
