# Checklist — skill-image-extraction

## Pre-ejecucion
- [ ] `skill-fifo-queue` completado (worker funcional)
- [ ] Tablas `extraction_runs`, `expense_records` existen
- [ ] Ollama corriendo con modelo Qwen3-VL cargado
- [ ] `uv add httpx` ejecutado
- [ ] Directorio `app/extraction/` creado
- [ ] Directorio `prompts/` creado
- [ ] Rama `arnes` activa

## Ejecucion — Prompt
- [ ] `prompts/expense_extraction.md` creado
- [ ] Prompt en espanol
- [ ] Especifica formato JSON con 5 campos + confidence
- [ ] Reglas claras: SOLO JSON, sin markdown, sin explicaciones
- [ ] transaction_type solo "Transferencia" o "Credito"
- [ ] Fecha en formato YYYY-MM-DD

## Ejecucion — Cliente Ollama
- [ ] `app/extraction/client.py` creado
- [ ] `OllamaClient` con base_url, model, timeout configurables
- [ ] `_load_prompt()` carga desde `prompts/expense_extraction.md`
- [ ] `extract_from_image()` usa httpx async
- [ ] Imagen codificada en base64
- [ ] Payload con temperature=0.1, num_predict=512
- [ ] Timeout manejado (httpx.TimeoutException)
- [ ] Conexion fallida manejada (httpx.ConnectError)

## Ejecucion — Parser
- [ ] `app/extraction/parser.py` creado
- [ ] `ExtractionResult` dataclass definido
- [ ] `parse_ollama_response()` extrae JSON de respuesta
- [ ] Maneja JSON dentro de bloques markdown (```json)
- [ ] Maneja JSON con regex fallback si parseo directo falla
- [ ] `validate_extraction()` revisa tipos y valores
- [ ] `normalize_extraction()` convierte a tipos Python
- [ ] Fecha: string -> date (YYYY-MM-DD)
- [ ] Monto: string/float -> Decimal(2 decimales)
- [ ] Banco: uppercase, trim
- [ ] Tipo: capitalize, validar contra lista permitida
- [ ] Campos faltantes -> None, no lanza excepcion
- [ ] Descripcion truncada a 500 chars

## Ejecucion — Confianza
- [ ] `app/extraction/confidence.py` creado
- [ ] `evaluate_confidence()` combina confianza del modelo + heuristicas
- [ ] Fecha futura -> baja confianza
- [ ] Monto = 0 -> baja confianza
- [ ] Banco = "DESCONOCIDO" -> confianza 0.1
- [ ] Descripcion < 3 chars -> baja confianza
- [ ] Confianza global (overall): promedio de campos
- [ ] Niveles PRD §16: Alta >= 0.90, Media 0.70-0.89, Baja < 0.70

## Ejecucion — Integracion con Worker
- [ ] `process_job()` en worker llama a `OllamaClient.extract_from_image()`
- [ ] Datos extraidos guardados en `expense_records`
- [ ] `confidence_json` guardado como JSON string
- [ ] `extraction_runs` creado con raw_response, parsed_json, is_valid_json, elapsed_ms
- [ ] Estado final basado en confianza:
  - [ ] overall >= 0.70 -> LISTO_PARA_REVISION
  - [ ] overall < 0.70 -> REQUIERE_REVISION
  - [ ] parseo fallido -> ERROR_PROCESAMIENTO

## Ejecucion — Manejo de errores
- [ ] `OllamaConnectionError` -> ERROR_PROCESAMIENTO
- [ ] `OllamaTimeoutError` -> ERROR_PROCESAMIENTO
- [ ] `InvalidJsonError` -> ERROR_PROCESAMIENTO (con raw_response guardado)
- [ ] Campos faltantes -> no fatal, se asignan null
- [ ] Modelo no cargado -> intentar pull, si falla ERROR_PROCESAMIENTO

## Ejecucion — Pruebas
- [ ] `scripts/validation/test_image_extraction.py` ejecutado
- [ ] Extraccion con imagen real: 5 campos extraidos
- [ ] Formato fecha: YYYY-MM-DD
- [ ] Formato monto: numero con 2 decimales
- [ ] transaction_type en {Transferencia, Credito}
- [ ] Imagen corrupta -> error manejado, no crashea
- [ ] Imagen no-ticket -> confianza baja
- [ ] Tiempo respuesta < 300s
- [ ] Lote de 10 imagenes: >= 99% JSON valido
- [ ] Confianza calculada para cada campo

## Post-ejecucion
- [ ] Evidencia `extraccion-imagenes.json` generada
- [ ] Evidencia `extraccion-imagenes.md` generada
- [ ] `skill-quality-gate` ejecutado
- [ ] `harness/PROGRESS.md` actualizado
