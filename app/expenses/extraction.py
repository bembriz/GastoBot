"""Extraccion con Gemini Flash — OCR, patrones visuales y analisis en un solo paso."""

import base64
import json
import os
import time
from datetime import datetime
from typing import Any

GEMINI_API_KEY = os.environ.get("GASTOSIA_GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GASTOSIA_GEMINI_MODEL", "gemini-2.5-flash")

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

PROMPT_EXTRACCION = f"""Analiza esta imagen de un ticket o comprobante bancario mexicano. Observa tanto el texto como los elementos visuales (colores, logos, interfaz) para identificar el banco.

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
- ticket_description: concepto breve, maximo una linea. Si el ticket es de tarjeta de credito con concepto BPK*, usa ese concepto
- bank: nombre del banco EMISOR (el que genero el comprobante), en MAYUSCULAS. Observa colores, logos y diseno de la interfaz. SIEMPRE intenta identificar el banco, aunque no este escrito explicitamente
- transaction_type: "Transferencia" si es envio de dinero, "Credito" si es deposito/abono
- Si no puedes identificar un campo con certeza, usa null"""


async def extract_from_image(image_path: str) -> dict[str, Any]:
    if not GEMINI_API_KEY:
        return {
            "raw_response": "",
            "parsed_json": None,
            "is_valid_json": False,
            "elapsed_ms": 0,
            "error_message": "Gemini API key no configurada",
        }

    t0 = time.monotonic()
    error_msg = None
    raw_response = ""
    parsed = None
    is_valid = False

    try:
        from google import genai

        with open(image_path, "rb") as f:
            image_data = f.read()

        mime = _guess_mime(image_path)

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[PROMPT_EXTRACCION, {"inline_data": {"mime_type": mime, "data": base64.b64encode(image_data).decode("utf-8")}}],
        )
        raw_response = response.text or ""
    except Exception as e:
        error_msg = f"Error Gemini: {e}"

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


def _guess_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".webp",):
        return "image/webp"
    return "image/jpeg"


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
        data["confidence"] = {k: 0.8 for k in ["transaction_date", "amount", "ticket_description", "bank", "transaction_type"]}

    return data
