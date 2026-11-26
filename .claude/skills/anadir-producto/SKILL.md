---
name: anadir-producto
description: Añade un producto al catálogo data/productos.yaml de granoytaza.es con todos los campos y comprobando que no esté repetido. Úsala cuando haya que meter un producto nuevo en el catálogo o en una guía.
argument-hint: "nombre del producto"
---

# Añadir un producto al catálogo

Producto: $ARGUMENTS

## Transparencia

- **El ASIN tiene que ser real y comprobado.** Si no lo puedes verificar, no pongas `asin:`;
  usa `buscar:` con el nombre exacto y dilo al terminar (el workflow de la API lista los ASIN
  encontrados para fijarlos después).
- `precio` es una referencia aproximada que solo sirve para filtrar y ordenar (no se muestra).
  Si no tienes una fuente para el precio, dilo y pon una estimación marcada como tal en el resumen final.
- `propio: true` solo si Eric ha dicho que lo usa. Nunca por suposición.

## Pasos

1. Busca en `data/productos.yaml` (por `id`, `nombre`, `asin` y marca) que no exista ya.
2. Elige `id`: minúsculas, guiones, marca o modelo corto (p. ej. `dedica-ec685`). Único.
3. Añade el bloque en la zona de su categoría, con el mismo formato que los vecinos:

```yaml
  - id: marca-modelo
    nombre: "Nombre comercial exacto"
    marca: "Marca"
    categoria: espresso   # una de las claves de "categorias" al principio del archivo
    gama: basica          # basica | media | alta
    precio: 0             # euros aproximados, solo para filtrar
    relevancia: 50        # 1-100, criterio editorial
    anadido: AAAA-MM-DD   # hoy
    asin: B0XXXXXXXX      # solo si está comprobado; si no, quita esta línea
    buscar: "Marca Modelo"
    resumen: "Una frase de por qué está en el catálogo."
    guia: guias/slug      # opcional, guía donde aparece
    # resena: resenas/slug   (si tiene reseña)
    # propio: true           (solo si Eric lo usa)
    # foto: img/archivo.jpg  (solo foto propia en static/img/)
```

4. `python3 build.py --preview` sin errores ni `AVISO` (el hook lo comprueba solo).
5. Resume qué campos están verificados y cuáles son estimaciones.
