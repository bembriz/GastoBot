"""benchmark_modelos.py — comparar Qwen3-VL 2B vs 4B con imágenes de ejemplos/.

Ejecutar: python scripts/validation/benchmark_modelos.py [--model 2b|4b] [--quick]

Requiere:
  - Ollama corriendo en localhost:11434
  - Modelos qwen3-vl:2b y qwen3-vl:4b descargados
  - Imágenes en ejemplos/
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
EJEMPLOS_DIR = PROJECT_ROOT / "ejemplos"
OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

PROMPT_EXTRACCION = """Analiza esta imagen de un ticket/comprobante bancario mexicano y extrae los siguientes campos en formato JSON:

{
  "transaction_date": "YYYY-MM-DD",
  "amount": 0.00,
  "ticket_description": "descripcion breve del gasto",
  "bank": "nombre del banco (NU, BANORTE, BBVA, etc.)",
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
- transaction_date: formato YYYY-MM-DD, usa la fecha del ticket, no la fecha actual
- amount: numero decimal, sin signo de pesos, solo el monto
- ticket_description: descripcion breve en español del concepto del gasto
- bank: nombre del banco en mayúsculas (NU, BANORTE, BBVA, etc.)
- transaction_type: SOLO "Transferencia" o "Crédito"
- confidence: numero entre 0.0 y 1.0 para cada campo indicando tu nivel de certeza

Responde ÚNICAMENTE con el JSON, sin texto adicional."""


def get_image_paths(quick: bool = False) -> list[Path]:
    """Obtener lista de imágenes del directorio ejemplos/."""
    extensions = {".jpg", ".jpeg", ".png", ".webp"}
    images = [
        p for p in EJEMPLOS_DIR.iterdir() if p.suffix.lower() in extensions and p.stat().st_size > 0
    ]
    images.sort()
    if quick:
        images = images[:25]
    return images


def image_to_base64(path: Path) -> str:
    """Convertir imagen a base64 para la API de Ollama."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_ollama(model: str, base64_image: str) -> dict:
    """Llamar a la API de Ollama con una imagen y devolver respuesta parseada."""
    import urllib.error
    import urllib.request

    payload = json.dumps(
        {
            "model": model,
            "prompt": PROMPT_EXTRACCION,
            "images": [base64_image],
            "stream": False,
        }
    ).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return {"error": f"URLError: {e.reason}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


def parse_json_response(response_text: str) -> tuple[dict | None, bool]:
    """Intentar extraer JSON válido de la respuesta del modelo."""
    text = response_text.strip()

    # Eliminar bloques de markdown
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    # Buscar primer { y último }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        data = json.loads(text)
        return data, True
    except json.JSONDecodeError:
        return None, False


def validate_extraction(data: dict | None, is_valid_json: bool) -> dict:
    """Validar estructura y campos de la extracción."""
    if not is_valid_json or data is None:
        return {
            "valid_json": False,
            "fields_present": [],
            "fields_missing": [],
            "types_valid": [],
            "types_invalid": [],
        }

    required = ["transaction_date", "amount", "ticket_description", "bank", "transaction_type"]
    present = [f for f in required if f in data]
    missing = [f for f in required if f not in data]

    # Validación de tipos básicos
    types_valid = []
    types_invalid = []
    for field in present:
        val = data.get(field)
        if field == "amount" and isinstance(val, (int, float)) or field == "transaction_date" and isinstance(val, str) or field in ("ticket_description", "bank", "transaction_type") and isinstance(val, str):
            types_valid.append(field)
        else:
            types_invalid.append(field)

    return {
        "valid_json": True,
        "fields_present": present,
        "fields_missing": missing,
        "types_valid": types_valid,
        "types_invalid": types_invalid,
    }


def benchmark_model(model: str, images: list[Path]) -> list[dict]:
    """Ejecutar benchmark para un modelo específico."""
    results = []
    print(f"\n{'=' * 40}")
    print(f"Benchmark: {model}")
    print(f"{'=' * 40}")

    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] {img_path.name} ({img_path.stat().st_size / 1024:.0f} KB)")

        try:
            t0 = time.monotonic()
            base64_img = image_to_base64(img_path)
            t1 = time.monotonic()

            response = call_ollama(model, base64_img)
            t2 = time.monotonic()

            if "error" in response:
                results.append(
                    {
                        "image": img_path.name,
                        "model": model,
                        "encode_ms": (t1 - t0) * 1000,
                        "inference_ms": (t2 - t1) * 1000,
                        "total_ms": (t2 - t0) * 1000,
                        "error": response["error"],
                        "valid_json": False,
                        "response_text": "",
                        "validation": {},
                    }
                )
                print(f"  [FAIL] {response['error']}")
                continue

            response_text = response.get("response", "")
            data, is_valid = parse_json_response(response_text)
            validation = validate_extraction(data, is_valid)

            results.append(
                {
                    "image": img_path.name,
                    "model": model,
                    "encode_ms": (t1 - t0) * 1000,
                    "inference_ms": (t2 - t1) * 1000,
                    "total_ms": (t2 - t0) * 1000,
                    "valid_json": is_valid,
                    "response_text": response_text[:500],
                    "extracted": data,
                    "validation": validation,
                }
            )

            status = "OK" if is_valid else "FAIL"
            fields = validation.get("fields_present", [])
            missing = validation.get("fields_missing", [])
            print(
                f"  [{status}] JSON={'OK' if is_valid else 'INVALID'} "
                f"| campos={len(fields)}/{len(fields) + len(missing)} "
                f"| t={(t2 - t0):.1f}s"
            )

        except Exception as e:
            results.append(
                {
                    "image": img_path.name,
                    "model": model,
                    "error": f"{type(e).__name__}: {str(e)}",
                    "valid_json": False,
                    "validation": {},
                }
            )
            print(f"  [FAIL] {type(e).__name__}: {e}")

    return results


def compute_metrics(results: list[dict], model: str) -> dict:
    """Calcular métricas agregadas para un modelo."""
    model_results = [r for r in results if r["model"] == model]
    total = len(model_results)
    valid_json = sum(1 for r in model_results if r.get("valid_json"))
    errors = sum(1 for r in model_results if "error" in r)

    times = [r.get("total_ms", 0) for r in model_results]
    avg_time = sum(times) / len(times) if times else 0

    # Campos presentes promedio
    fields_counts = [len(r.get("validation", {}).get("fields_present", [])) for r in model_results]
    avg_fields = sum(fields_counts) / len(fields_counts) if fields_counts else 0

    return {
        "model": model,
        "total_images": total,
        "valid_json": valid_json,
        "valid_json_pct": (valid_json / total * 100) if total > 0 else 0,
        "errors": errors,
        "avg_total_ms": round(avg_time, 0),
        "avg_fields_present": round(avg_fields, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark Qwen3-VL modelos")
    parser.add_argument("--quick", action="store_true", help="Solo 25 imagenes")
    parser.add_argument("--model", choices=["2b", "4b"], help="Solo un modelo")
    parser.add_argument("--output", type=str, help="Archivo JSON de salida")
    args = parser.parse_args()

    # Verificar Ollama
    try:
        import urllib.request

        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            available_models = [m["name"] for m in data.get("models", [])]
            print(f"[OK] Ollama accesible en {OLLAMA_URL}")
            print(f"[OK] Modelos disponibles: {', '.join(available_models[:10])}")
    except Exception as e:
        print(f"[FAIL] Ollama no accesible en {OLLAMA_URL}: {e}")
        print("[INFO] Instale Ollama con: curl -fsSL https://ollama.com/install.sh | sh")
        return 1

    # Obtener imágenes
    images = get_image_paths(quick=args.quick)
    if not images:
        print(f"[FAIL] No se encontraron imágenes en {EJEMPLOS_DIR}")
        return 1
    print(f"[OK] {len(images)} imágenes encontradas para benchmark")

    # Ejecutar benchmark
    all_results: list[dict] = []
    models_to_test = ["qwen3-vl:2b", "qwen3-vl:4b"]

    if args.model == "2b":
        models_to_test = ["qwen3-vl:2b"]
    elif args.model == "4b":
        models_to_test = ["qwen3-vl:4b"]

    for model in models_to_test:
        if model not in available_models:
            print(f"[WARN] Modelo {model} no disponible, omitiendo")
            continue
        results = benchmark_model(model, images)
        all_results.extend(results)

    if not all_results:
        print("[FAIL] No se ejecutaron benchmarks (ningún modelo disponible)")
        return 1

    # Calcular métricas finales
    print("\n" + "=" * 60)
    print("RESULTADOS FINALES")
    print("=" * 60)

    for model in models_to_test:
        metrics = compute_metrics(all_results, model)
        print(f"\n{model}:")
        print(f"  Imágenes: {metrics['total_images']}")
        print(
            f"  JSON válido: {metrics['valid_json']}/{metrics['total_images']} ({metrics['valid_json_pct']:.1f}%)"
        )
        print(f"  Errores: {metrics['errors']}")
        print(f"  Tiempo promedio: {metrics['avg_total_ms']:.0f}ms")
        print(f"  Campos promedio: {metrics['avg_fields_present']}/5")

    # Guardar resultados
    output_path = (
        Path(args.output)
        if args.output
        else PROJECT_ROOT / "harness" / "evidence" / "fase0" / "benchmark-modelos.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "ollama_url": OLLAMA_URL,
        "models_tested": models_to_test,
        "total_images": len(images),
        "quick_mode": args.quick,
        "results": all_results,
        "metrics": {m: compute_metrics(all_results, m) for m in models_to_test},
    }
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Resultados guardados en {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
