"""Extraccion multimodal — analisis de imagenes con Ollama + Qwen3-VL.

Envia imagenes a Ollama, parsea y valida la respuesta JSON,
normaliza campos y calcula nivel de confianza.
"""

import json
import os
import time
from typing import Any

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("GASTOSIA_OLLAMA_MODEL", "qwen3-vl:4b")
OLLAMA_TIMEOUT = int(os.environ.get("GASTOSIA_OLLAMA_TIMEOUT", "300"))

PROMPT_EXTRACCION = """Analiza esta imagen de un ticket/comprobante bancario mexicano y extrae los siguientes campos en formato JSON:

{
  "transaction_date": "YYYY-MM-DD",
  "amount": 0.00,
  "ticket_description": "descripcion breve del gasto en espanol",
  "bank": "nombre del banco (NU, BANORTE, BBVA, HEYBANCO, etc.)",
  "transaction_type": "Transferencia|Credito",
  "confidence": {
    "transaction_date": 0.0,
    "amount": 0.0,
    "ticket_description": 0.0,
    "bank": 0.0,
    "transaction_type": 0.0
  }
}

Reglas:
- transaction_date: usa la fecha del ticket en formato YYYY-MM-DD, NO la fecha actual
- amount: SOLO el numero decimal, sin signo de pesos ni comillas
- ticket_description: descripcion breve en espanol del concepto del gasto
- bank: nombre del banco en MAYUSCULAS
- transaction_type: SOLO "Transferencia" o "Credito"
- confidence: numero entre 0.0 y 1.0 indicando tu nivel de certeza para cada campo

Responde UNICAMENTE con el JSON, sin ningun otro texto."""


async def extract_from_image(image_path: str) -> dict[str, Any]:
    import base64

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    t0 = time.monotonic()
    error_msg = None
    raw_response = ""
    parsed = None
    is_valid = False

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": PROMPT_EXTRACCION,
                    "images": [image_b64],
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_response = data.get("response", "")
    except httpx.TimeoutException:
        error_msg = "Timeout de Ollama"
    except httpx.HTTPError as e:
        error_msg = f"Error HTTP Ollama: {e}"
    except Exception as e:
        error_msg = f"Error inesperado: {e}"

    elapsed_ms = int((time.monotonic() - t0) * 1000)

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
    }


def _parse_json_response(text: str) -> tuple[dict | None, bool]:
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


def _normalize_extraction(data: dict) -> dict:
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
        data["confidence"] = {k: 0.5 for k in ["transaction_date", "amount", "ticket_description", "bank", "transaction_type"]}

    return data
