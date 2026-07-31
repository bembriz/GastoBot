#!/usr/bin/env python3
"""
Ejemplo de llamada a Ollama API para extraccion de gastos desde imagen.

NO usar en produccion. Solo como referencia para el benchmark de Fase 0.
"""

import base64
import json
import time
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPT = """Analiza esta imagen de un ticket/comprobante bancario y extrae los siguientes campos en formato JSON:

{
  "transaction_date": "YYYY-MM-DD",
  "amount": 0.00,
  "ticket_description": "descripcion del gasto o concepto",
  "bank": "nombre del banco",
  "transaction_type": "Transferencia o Credito",
  "confidence": {
    "transaction_date": 0.0,
    "amount": 0.0,
    "ticket_description": 0.0,
    "bank": 0.0,
    "transaction_type": 0.0
  }
}

Reglas:
- transaction_date: fecha de la transaccion en formato ISO 8601
- amount: monto numerico, sin simbolo de moneda, con punto decimal
- ticket_description: descripcion breve del concepto o establecimiento
- bank: nombre del banco (NU, Santander, BBVA, etc.) o "DESCONOCIDO"
- transaction_type: SOLO "Transferencia" o "Credito"
- confidence: numero entre 0.0 y 1.0 indicando que tan seguro estas de cada campo
- Si no puedes determinar un campo, usa null para el valor y 0.0 para confidence
- Responde UNICAMENTE con el JSON, sin texto adicional, sin markdown, sin explicaciones"""


def encode_image(image_path: str) -> str:
    """Codifica una imagen en base64 para enviar a Ollama."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_ollama(image_path: str, model: str = "qwen3-vl:4b", timeout: int = 300) -> dict:
    """
    Envia una imagen a Ollama y retorna el JSON parseado.

    Args:
        image_path: Ruta a la imagen
        model: Nombre del modelo en Ollama
        timeout: Timeout en segundos

    Returns:
        dict con campos extraidos y metadata de la llamada

    Raises:
        requests.Timeout: Si Ollama no responde a tiempo
        json.JSONDecodeError: Si la respuesta no es JSON valido
        ValueError: Si faltan campos requeridos
    """
    image_b64 = encode_image(image_path)

    payload = {
        "model": model,
        "prompt": PROMPT,
        "images": [image_b64],
        "stream": False,
        "options": {
            "temperature": 0.1,  # Baja temperatura para respuestas deterministas
        },
    }

    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    response.raise_for_status()
    elapsed = time.time() - start_time

    raw = response.json()
    response_text = raw.get("response", "")

    # Limpiar respuesta: extraer solo el JSON
    response_text = response_text.strip()
    if response_text.startswith("```"):
        # Quitar bloques de codigo markdown
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        # Intentar extraer JSON de la respuesta con regex
        import re

        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise

    # Validar campos requeridos
    required_fields = [
        "transaction_date",
        "amount",
        "ticket_description",
        "bank",
        "transaction_type",
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise ValueError(f"Campos faltantes en respuesta: {missing}")

    # Normalizar tipos
    if data.get("amount") is not None:
        data["amount"] = float(data["amount"])

    if data.get("transaction_type") is not None:
        tt = data["transaction_type"].strip().capitalize()
        if tt not in ("Transferencia", "Credito"):
            data["transaction_type"] = None

    return {
        "model": model,
        "image_path": str(image_path),
        "elapsed_seconds": round(elapsed, 2),
        "raw_response": raw.get("response", ""),
        "extracted": data,
        "eval_count": raw.get("eval_count"),
        "eval_duration": raw.get("eval_duration"),
    }


# Ejemplo de uso
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} <imagen.jpg> [modelo]")
        print("  Modelos disponibles: qwen3-vl:2b, qwen3-vl:4b")
        sys.exit(1)

    image_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "qwen3-vl:4b"

    if not Path(image_path).exists():
        print(f"Error: archivo no encontrado: {image_path}")
        sys.exit(1)

    try:
        result = call_ollama(image_path, model)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except requests.ConnectionError:
        print("Error: No se pudo conectar a Ollama. Verifica que este corriendo.")
        sys.exit(1)
    except requests.Timeout:
        print(
            f"Error: Timeout despues de {300}s. La imagen puede ser muy grande o el modelo muy lento."
        )
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Ollama respondio pero no se pudo parsear el JSON.")
        sys.exit(1)
    except ValueError as e:
        print(f"Error de validacion: {e}")
        sys.exit(1)
