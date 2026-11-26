#!/usr/bin/env python3
"""PostToolUse: tras editar contenido, catálogo o el generador, compila la vista previa.

Si el build falla o avisa de algo (por ejemplo, un producto que no está en el catálogo),
devuelve el error a Claude (código 2) para que lo arregle antes de seguir.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
path = (data.get("tool_input") or {}).get("file_path") or ""
if not path:
    sys.exit(0)
try:
    rel = Path(path).resolve().relative_to(root).as_posix()
except ValueError:
    sys.exit(0)

VIGILADOS = ("content/", "data/", "static/")
if not (rel.startswith(VIGILADOS) or rel in ("build.py", "site.yaml")):
    sys.exit(0)

try:
    r = subprocess.run([sys.executable, "build.py", "--preview"], cwd=root,
                       capture_output=True, text=True, timeout=60)
except subprocess.TimeoutExpired:
    print("El build de la vista previa ha tardado más de 60 s y se ha cortado.", file=sys.stderr)
    sys.exit(2)

salida = (r.stdout + r.stderr).strip()
avisos = [l for l in salida.splitlines() if l.startswith("AVISO")]
if r.returncode != 0:
    print(f"build.py --preview ha fallado tras editar {rel}:\n{salida[-3000:]}", file=sys.stderr)
    sys.exit(2)
if avisos:
    print(f"build.py --preview avisa tras editar {rel}:\n" + "\n".join(avisos), file=sys.stderr)
    sys.exit(2)
sys.exit(0)
