#!/usr/bin/env python3
"""PreToolUse: bloquea cambios que pueden tirar la web o las comisiones.

- static/CNAME: si cambia, granoytaza.es deja de servir la web.
- data/amazon.json: lo genera scripts/amazon_api.py; editarlo a mano es inventar precios.
- site.yaml: se puede editar, pero el tag de afiliado tiene que seguir siendo granoytaza-21.
"""
import json
import os
import re
import sys
from pathlib import Path

TAG = "granoytaza-21"

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

inp = data.get("tool_input") or {}
path = inp.get("file_path") or ""
if not path:
    sys.exit(0)
root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
try:
    rel = Path(path).resolve().relative_to(root).as_posix()
except ValueError:
    sys.exit(0)


def bloquear(motivo):
    print(motivo, file=sys.stderr)
    sys.exit(2)


if rel == "static/CNAME":
    bloquear("static/CNAME está protegido: si cambia, el dominio granoytaza.es deja de funcionar. "
             "Si de verdad hay que cambiarlo, pídeselo a Eric para que lo haga él.")
if rel == "data/amazon.json":
    bloquear("data/amazon.json lo genera scripts/amazon_api.py con datos reales de Amazon. "
             "No se edita a mano (serían precios inventados).")

if rel == "site.yaml":
    if data.get("tool_name") == "Write":
        nuevo = inp.get("content", "")
        if f'amazon_tag: "{TAG}"' not in nuevo:
            bloquear(f'site.yaml tiene que conservar  amazon_tag: "{TAG}"  (es el ID de afiliado).')
    else:
        cambios = inp.get("edits") or [inp]
        for c in cambios:
            viejo, nuevo = c.get("old_string", ""), c.get("new_string", "")
            if "amazon_tag" in viejo and f'amazon_tag: "{TAG}"' not in nuevo:
                bloquear(f'No se puede cambiar ni quitar amazon_tag en site.yaml (debe ser "{TAG}").')
            if re.search(r"^\s*amazon_tag\s*:", nuevo, re.M) and "amazon_tag" not in viejo:
                bloquear("No se puede añadir otro amazon_tag a site.yaml.")
sys.exit(0)
