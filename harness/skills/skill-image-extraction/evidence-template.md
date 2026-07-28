# Evidence Report — skill-image-extraction

> **Skill:** `skill-image-extraction`
> **Fase:** `fase1`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{Summary: Ollama integration with Qwen3-VL, structured prompt, JSON parser, confidence evaluation, and worker integration.}

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Modelo utilizado | {qwen3-vl:2b | qwen3-vl:4b} |
| Timeout configurado | 300s |
| % JSON valido en pruebas | {N}% |
| Tiempo promedio extraccion | {N}s |
| Campos extraidos | 5 (+ confidence) |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecucion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Tablas extraction_runs, expense_records | {status} | {N} columnas |
| C2 | Ollama corriendo | {status} | Modelo: {model} |
| C3 | Dependencias instaladas | {status} | httpx |

### Ejecucion — Prompt

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `prompts/expense_extraction.md` existe | {status} | {N} lineas |
| C2 | Prompt en espanol | {status} | Idioma verificado |
| C3 | Especifica formato JSON exacto | {status} | 5 campos + confidence |
| C4 | Reglas de solo JSON | {status} | Sin markdown, sin explicaciones |

### Ejecucion — Cliente Ollama

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `OllamaClient` implementado | {status} | Async con httpx |
| C2 | Codificacion base64 | {status} | Imagen encodeada |
| C3 | Payload correcto | {status} | temperature=0.1, stream=False |
| C4 | Timeout configurable | {status} | Default 300s |
| C5 | `OllamaConnectionError` manejado | {status} | httpx.ConnectError |
| C6 | `OllamaTimeoutError` manejado | {status} | httpx.TimeoutException |

### Ejecucion — Parser

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `parse_ollama_response()` funcional | {status} | JSON limpio |
| C2 | Markdown ```json bloqueado | {status} | Limpieza funcionando |
| C3 | Regex fallback | {status} | JSON entre llaves |
| C4 | `normalize_extraction()`: fecha | {status} | string -> date |
| C5 | `normalize_extraction()`: monto | {status} | -> Decimal(2) |
| C6 | `normalize_extraction()`: banco | {status} | uppercase, trim |
| C7 | `normalize_extraction()`: tipo | {status} | Validado contra lista |
| C8 | Campos faltantes -> None | {status} | No lanza excepcion |
| C9 | Descripcion truncada 500 chars | {status} | {detail} |

### Ejecucion — Confianza

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Confianza del modelo usada | {status} | Si existe en respuesta |
| C2 | Heuristica: fecha futura | {status} | Baja confianza |
| C3 | Heuristica: monto = 0 | {status} | Baja confianza |
| C4 | Heuristica: banco DESCONOCIDO | {status} | Confianza 0.1 |
| C5 | Confianza global (overall) | {status} | Promedio de campos |
| C6 | Niveles PRD §16 correctos | {status} | Alta/Media/Baja |

### Ejecucion — Pruebas

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | 5 campos extraidos de imagen real | {status} | Fecha, monto, desc, banco, tipo |
| C2 | Formato fecha: YYYY-MM-DD | {status} | ISO 8601 |
| C3 | Formato monto: numero, 2 decimales | {status} | Decimal |
| C4 | Tipo en {Transferencia, Credito} | {status} | Valores validos |
| C5 | Imagen corrupta manejada | {status} | No crashea |
| C6 | Imagen no-ticket -> confianza baja | {status} | overall < 0.70 |
| C7 | Tiempo respuesta < 300s | {status} | {N}s promedio |
| C8 | Lote 10 imagenes >= 99% JSON valido | {status} | {N}% |

---

## Resultados de Extraccion (Muestra)

| Imagen | Fecha | Monto | Banco | Tipo | Confianza |
|---|---|---|---|---|---|
| {file1} | {date} | {amount} | {bank} | {type} | {confidence} |
| {file2} | {date} | {amount} | {bank} | {type} | {confidence} |
| ... | ... | ... | ... | ... | ... |

---

## Artefactos Generados

| Archivo | Tipo | Descripcion |
|---|---|---|
| `prompts/expense_extraction.md` | config | Prompt estructurado |
| `app/extraction/client.py` | source | Cliente Ollama async |
| `app/extraction/parser.py` | source | Parser y validador JSON |
| `app/extraction/confidence.py` | source | Calculo de confianza |
| `scripts/validation/test_image_extraction.py` | script | Pruebas de extraccion |
| `harness/evidence/fase1/extraccion-imagenes.json` | report | Evidencia JSON |
| `harness/evidence/fase1/extraccion-imagenes.md` | report | Evidencia Markdown |

---

## Errores (si los hay)

| Codigo | Mensaje |
|---|---|
| `ERR_XXX` | {description} |

---

## Advertencias (si las hay)

- {warning}

---

## Proximos Pasos

1. Completar Fase 1 con `skill-fase1-nucleo` (cierre)
2. Ajustar prompt segun resultados de pruebas
3. Considerar fine-tuning del prompt para tipos de ticket especificos

---

## Precondiciones al Inicio

```json
{
  "fifo_queue_skill_completed": true,
  "extraction_runs_table_exists": true,
  "ollama_running": true,
  "model_loaded": "{qwen3-vl:2b|qwen3-vl:4b}",
  "httpx_installed": true
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
