"""Extraccion multimodal — Gemini multi-key -> Kimi (fallback en cadena)."""

import base64
import json
import os
import time
from typing import Any

GEMINI_MODEL = os.environ.get("GASTOSIA_GEMINI_MODEL", "gemini-2.0-flash")

KIMI_API_KEY = os.environ.get("GASTOSIA_KIMI_API_KEY", "").strip()
KIMI_MODEL = os.environ.get("GASTOSIA_KIMI_MODEL", "kimi-k2.6")
KIMI_BASE = "https://api.moonshot.ai/v1/chat/completions"


def _collect_gemini_keys() -> list[str]:
    keys: list[str] = []
    for i in range(1, 10):
        key = os.environ.get(f"GASTOSIA_GEMINI_API_KEY_{i}", "").strip()
        if key:
            keys.append(key)
    return keys


GEMINI_API_KEYS = _collect_gemini_keys()

BANK_HINTS = """
Bancos frecuentes y como identificarlos en la imagen:
- NU: fondo oscuro/morado, interfaz minimalista, logo de "nU" o "Nu"
- HEYBANCO: fondo blanco con acentos naranjas/rojos, tipografia moderna, logo circular naranja
- BANORTE: fondo verde, logo con aguila, interfaz tradicional de banca
- BBVA: fondo azul, logo BBVA azul, comprobantes de transferencia con diseno corporativo
- HSBC: fondo rojo, logo hexagonal rojo y blanco
- SANTANDER: fondo rojo, logo con llama, interfaz corporativa
- BANAMEX/CITIBANAMEX: fondo azul marino, logo de Citibanamex
"""

_TICKET_HINT = (
    "concepto breve, maximo una linea. Si el ticket es de tarjeta de "
    "credito con concepto BPK*, usa ese concepto"
)
_BANK_HINT = (
    "nombre del banco EMISOR (el que genero el comprobante), en MAYUSCULAS. "
    "Observa colores, logos y diseno de la interfaz. SIEMPRE intenta identificar "
    "el banco, aunque no este escrito explicitamente"
)

PROMPT_EXTRACCION = f"""Analiza esta imagen de un ticket o comprobante bancario mexicano. \
Observa tanto el texto como los elementos visuales (colores, logos, interfaz) para \
identificar el banco.

{BANK_HINTS}

Devuelve SOLO un JSON sin markdown ni explicaciones:

{{
  "transaction_date": "YYYY-MM-DD",
  "amount": 0.00,
  "ticket_description": "descripcion breve en espanol",
  "bank": "NOMBRE_DEL_BANCO",
  "transaction_type": "Transferencia|Credito"
}}

Reglas IMPORTANTES:
- transaction_date: fecha del ticket en YYYY-MM-DD, inferir del contexto visual si no hay texto
- amount: SOLO numero decimal, sin signo de pesos ni comillas
- ticket_description: {_TICKET_HINT}
- bank: {_BANK_HINT}
- transaction_type: "Transferencia" si es envio de dinero, "Credito" si es deposito/abono
- Si no puedes identificar un campo con certeza, usa null"""


async def _gemini_extract(image_path: str, mime: str, api_key: str) -> dict[str, Any]:
    from google import genai

    with open(image_path, "rb") as f:
        image_data = f.read()

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[  # type: ignore[arg-type]
            PROMPT_EXTRACCION,
            {
                "inline_data": {
                    "mime_type": mime,
                    "data": base64.b64encode(image_data).decode("utf-8"),
                }
            },
        ],
    )
    return {
        "raw_response": response.text or "",
        "engine": "gemini",
        "error_message": None,
    }


async def _kimi_extract(image_path: str, mime: str) -> dict[str, Any]:
    import httpx

    with open(image_path, "rb") as f:
        image_data = f.read()

    encoded = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime};base64,{encoded}"

    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": KIMI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": PROMPT_EXTRACCION},
                ],
            }
        ],
        "thinking": {"type": "disabled"},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(KIMI_BASE, headers=headers, json=body)

    if resp.status_code != 200:
        return {
            "raw_response": "",
            "engine": "kimi",
            "error_message": f"Kimi error {resp.status_code}: {resp.text[:200]}",
        }

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return {
        "raw_response": content,
        "engine": "kimi",
        "error_message": None,
    }


async def extract_from_image(image_path: str) -> dict[str, Any]:
    t0 = time.monotonic()
    collected_errors: list[str] = []
    mime = _guess_mime(image_path)

    # 1. Probar todas las keys de Gemini
    for i, key in enumerate(GEMINI_API_KEYS):
        label = f"Gemini({i + 1})"
        try:
            result = await _gemini_extract(image_path, mime, key)
            if not result.get("error_message"):
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                return _build_response(result["raw_response"], elapsed_ms, "gemini", None)
            collected_errors.append(f"{label}: {result['error_message']}")
        except Exception as e:
            err_str = str(e)
            if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                collected_errors.append(f"{label}: cuota agotada")
                print(f"[Extraction] {label} sin cuota, probando siguiente...", flush=True)
            else:
                collected_errors.append(f"{label}: {err_str[:120]}")
                print(f"[Extraction] {label} error: {err_str[:120]}", flush=True)

    # 2. Kimi como ultimo recurso
    if KIMI_API_KEY:
        try:
            result = await _kimi_extract(image_path, mime)
            if not result.get("error_message"):
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                return _build_response(result["raw_response"], elapsed_ms, "kimi", None)
            collected_errors.append(f"Kimi: {result['error_message']}")
        except Exception as e:
            collected_errors.append(f"Kimi: {e!s:.120}")
    else:
        collected_errors.append("Kimi: no configurado")

    error_msg = " | ".join(collected_errors) if collected_errors else "Ningun motor configurado"
    print(f"[Extraction] Todos los motores fallaron: {error_msg}", flush=True)

    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return _build_response("", elapsed_ms, None, error_msg)


def _build_response(
    raw_response: str, elapsed_ms: int, engine: str | None, error_msg: str | None
) -> dict[str, Any]:
    parsed = None
    is_valid = False

    if raw_response and not error_msg:
        parsed, is_valid = _parse_json_response(raw_response)

    if parsed:
        parsed = _normalize_extraction(parsed)

    return {
        "raw_response": raw_response,
        "parsed_json": parsed,
        "is_valid_json": is_valid,
        "elapsed_ms": elapsed_ms,
        "error_message": error_msg,
        "engine": engine,
    }


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".webp",):
        return "image/webp"
    return "image/jpeg"


def _parse_json_response(text: str) -> tuple[dict[str, Any] | None, bool]:
    text = text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        data = json.loads(text)
        required = ["transaction_date", "amount", "ticket_description", "bank", "transaction_type"]
        if all(k in data for k in required):
            return data, True
        return data, False
    except json.JSONDecodeError:
        return None, False


def _normalize_extraction(data: dict[str, Any]) -> dict[str, Any]:
    if "amount" in data and isinstance(data["amount"], str):
        try:
            data["amount"] = float(data["amount"].replace("$", "").replace(",", ""))
        except (ValueError, TypeError):
            data["amount"] = 0.0

    if "transaction_type" in data:
        tt = str(data["transaction_type"]).strip().lower()
        if "credito" in tt or "crédito" in tt:
            data["transaction_type"] = "Credito"
        else:
            data["transaction_type"] = "Transferencia"

    if "bank" in data:
        data["bank"] = str(data["bank"]).strip().upper()

    if "confidence" not in data:
        data["confidence"] = {
            k: 0.8
            for k in [
                "transaction_date",
                "amount",
                "ticket_description",
                "bank",
                "transaction_type",
            ]
        }

    return data
