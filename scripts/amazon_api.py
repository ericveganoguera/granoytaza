#!/usr/bin/env python3
"""Actualiza precios, imágenes y enlaces del catálogo con la Creators API de Amazon.

Credenciales (variables de entorno; en GitHub van como "secrets"):
  AMAZON_CREDENTIAL_ID       Credential ID de Associates Central > Herramientas > Creators API
  AMAZON_CREDENTIAL_SECRET   Credential Secret
  AMAZON_CREDENTIAL_VERSION  Versión que muestra Amazon junto a la credencial (por defecto 3.2, Europa)

Uso:
  python3 scripts/amazon_api.py              -> escribe data/amazon.json
  python3 scripts/amazon_api.py --comprobar  -> solo comprueba si tu cuenta tiene acceso

Sin credenciales o sin acceso, termina sin error y la web usa los rangos de precio.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = yaml.safe_load((ROOT / "site.yaml").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "amazon.json"
API = "https://creatorsapi.amazon/catalog/v1"
TOKEN_URLS = {
    "3.1": "https://api.amazon.com/auth/o2/token",      # Norteamérica
    "3.2": "https://api.amazon.co.uk/auth/o2/token",    # Europa (incluye amazon.es)
    "3.3": "https://api.amazon.co.jp/auth/o2/token",    # Lejano Oriente
}
RESOURCES = ["itemInfo.title", "images.primary.large", "images.primary.medium",
             "offersV2.listings.price", "offersV2.listings.availability"]
MARKET = CFG["amazon_domain"]
TAG = CFG["amazon_tag"]


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__(f"HTTP {status}: {body[:400]}")
        self.status, self.body = status, body


def post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise ApiError(e.code, e.read().decode(errors="replace")) from None


def get_token():
    cid = os.environ.get("AMAZON_CREDENTIAL_ID", "").strip()
    secret = os.environ.get("AMAZON_CREDENTIAL_SECRET", "").strip()
    version = os.environ.get("AMAZON_CREDENTIAL_VERSION", "").strip() or "3.2"
    if not cid or not secret:
        return None
    url = TOKEN_URLS.get(version, TOKEN_URLS["3.2"])
    data = post(url, {"grant_type": "client_credentials", "client_id": cid,
                      "client_secret": secret, "scope": "creatorsapi::default"}, {})
    return data["access_token"]


def call(token, op, body):
    body = {"partnerTag": TAG, "marketplace": MARKET, **body}
    return post(f"{API}/{op}", body, {"Authorization": f"Bearer {token}", "x-marketplace": MARKET})


def items_of(resp):
    for key in ("itemsResult", "searchResult", "ItemsResult", "SearchResult"):
        if isinstance(resp.get(key), dict):
            return resp[key].get("items") or resp[key].get("Items") or []
    return []


def extract(item):
    def dig(obj, *path):
        for k in path:
            if isinstance(obj, list):
                obj = obj[0] if obj else None
            if not isinstance(obj, dict):
                return None
            obj = obj.get(k)
        return obj
    listing = dig(item, "offersV2", "listings")
    listing = listing[0] if isinstance(listing, list) and listing else {}
    money = dig(listing, "price", "money") or {}
    return {
        "asin": item.get("asin") or item.get("ASIN"),
        "titulo": dig(item, "itemInfo", "title", "displayValue"),
        "imagen": dig(item, "images", "primary", "large", "url") or dig(item, "images", "primary", "medium", "url"),
        "url": item.get("detailPageURL"),
        "precio": money.get("amount"),
        "precio_texto": money.get("displayAmount"),
        "disponibilidad": dig(listing, "availability", "message"),
    }


def explain(err):
    txt = err.body if isinstance(err, ApiError) else str(err)
    low = txt.lower()
    if "eligib" in low or "notelig" in low or "qualif" in low:
        return ("Tu cuenta todavía NO tiene acceso a la API: Amazon exige al menos 10 ventas "
                "cualificadas en los últimos 30 días. La web seguirá usando rangos de precio.")
    if "invalid_client" in low or (isinstance(err, ApiError) and err.status == 401):
        return "Las credenciales no son válidas. Revisa el Credential ID, el Secret y la versión."
    if isinstance(err, ApiError) and err.status == 429:
        return "Amazon ha limitado las peticiones (demasiadas seguidas). Se reintentará en la próxima ejecución."
    return f"Respuesta inesperada de Amazon: {txt[:300]}"


def comprobar():
    try:
        token = get_token()
    except Exception as e:  # noqa: BLE001
        print("❌", explain(e)); return 0
    if not token:
        print("❌ No hay credenciales. Añade AMAZON_CREDENTIAL_ID y AMAZON_CREDENTIAL_SECRET como secrets del repositorio.")
        return 0
    try:
        resp = call(token, "searchItems", {"keywords": "cafetera", "itemCount": 1, "resources": RESOURCES})
        found = items_of(resp)
        print("✅ Acceso correcto a la API de Amazon.", f"Ejemplo: {extract(found[0])['titulo']}" if found else "")
    except Exception as e:  # noqa: BLE001
        print("❌", explain(e))
    return 0


def main():
    cat = yaml.safe_load((ROOT / "data" / "productos.yaml").read_text(encoding="utf-8"))["productos"]
    try:
        token = get_token()
    except Exception as e:  # noqa: BLE001
        print("Sin acceso a la API:", explain(e)); return 0
    if not token:
        print("Sin credenciales de Amazon: la web usará rangos de precio."); return 0

    result, sugerencias = {}, []
    con_asin = [p for p in cat if p.get("asin")]
    try:
        for i in range(0, len(con_asin), 10):  # getItems admite hasta 10 ASIN por petición
            lote = con_asin[i:i + 10]
            resp = call(token, "getItems", {"itemIds": [p["asin"] for p in lote],
                                            "itemIdType": "ASIN", "resources": RESOURCES})
            by_asin = {d["asin"]: d for d in map(extract, items_of(resp))}
            for p in lote:
                if p["asin"] in by_asin:
                    result[p["id"]] = by_asin[p["asin"]]
            time.sleep(1.1)
        for p in cat:
            if p.get("asin") or not p.get("buscar"):
                continue
            resp = call(token, "searchItems", {"keywords": p["buscar"], "itemCount": 3,
                                               "searchIndex": "All", "resources": RESOURCES})
            marca = (p.get("marca") or "").lower().replace("'", "")
            for d in map(extract, items_of(resp)):
                if d["titulo"] and marca and marca in d["titulo"].lower().replace("'", ""):
                    result[p["id"]] = d
                    sugerencias.append(f"  {p['id']}: asin: {d['asin']}   # {d['titulo'][:70]}")
                    break
            time.sleep(1.1)
    except Exception as e:  # noqa: BLE001
        print("La API ha fallado:", explain(e))
        if not result:
            return 0

    OUT.write_text(json.dumps({"actualizado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                               "items": result}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: datos de Amazon para {len(result)} de {len(cat)} productos en {OUT}")
    if sugerencias:
        print("ASIN encontrados por búsqueda (cópialos en data/productos.yaml para fijarlos):")
        print("\n".join(sugerencias))
    return 0


if __name__ == "__main__":
    sys.exit(comprobar() if "--comprobar" in sys.argv else main())
