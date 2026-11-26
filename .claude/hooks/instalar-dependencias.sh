#!/usr/bin/env bash
# SessionStart: instala lo que necesita build.py si falta (pasa en las sesiones en la nube).
if python3 -c "import markdown, yaml" 2>/dev/null; then
  exit 0
fi
if pip install -q markdown pyyaml >/dev/null 2>&1 || pip install -q --user markdown pyyaml >/dev/null 2>&1; then
  echo "Instaladas las dependencias del build (markdown, pyyaml)."
else
  echo "AVISO: no se pudieron instalar markdown y pyyaml; build.py no funcionará hasta instalarlas."
fi
exit 0
