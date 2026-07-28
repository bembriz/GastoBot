# Evidence Report — skill-fase0-tecnica

> **Skill:** `skill-fase0-tecnica`
> **Fase:** `fase0`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{One-paragraph summary covering all 5 validations: secrets mechanism, PostgreSQL, Google Sheets, historical import, and model benchmark. Include the recommended model and whether the phase is cleared to proceed to Fase 1.}

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Imagenes procesadas en benchmark | {N} |
| Modelos comparados | 2 (qwen3-vl:2b, qwen3-vl:4b) |
| Tiempo total de benchmark | {hh:mm:ss} |
| Errores | {N} |
| Advertencias | {N} |

---

## 1. Validacion de Secretos

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `.env.example` contiene 14 variables | {status} | {detail} |
| C2 | Ninguna variable tiene valor real | {status} | {detail} |
| C3 | `os.environ.get("GASTOSIA_*")` funcional | {status} | {detail} |
| C4 | `GASTOSIA_SESSION_SECRET` >= 32 chars | {status} | {detail} |
| C5 | Variables obligatorias no vacias | {status} | {detail} |
| C6 | Secretos enmascarados en output | {status} | {detail} |
| C7 | Script falla si falta variable obligatoria | {status} | {detail} |

## 2. Validacion de PostgreSQL

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Conexion establecida | {status} | Host: {host}, Port: {port} |
| C2 | Version PostgreSQL | {status} | {version} |
| C3 | Base `gastos_ia` creada | {status} | {detail} |
| C4 | Usuario `gastos_app` creado | {status} | {detail} |
| C5 | Permisos CONNECT otorgados | {status} | {detail} |
| C6 | Permisos CREATE en schema public | {status} | {detail} |
| C7 | Creacion/eliminacion de tabla de prueba | {status} | {detail} |
| C8 | `pg_stat_activity` muestra conexion | {status} | {detail} |

## 3. Validacion de Google Sheets

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Autenticacion con cuenta de servicio | {status} | {detail} |
| C2 | Apertura del spreadsheet por ID | {status} | {detail} |
| C3 | Listado de pestanas existentes | {status} | {N} pestanas |
| C4 | `_Control` existe o se creo | {status} | {detail} |
| C5 | Pestana `_Test_Fase0` creada con 16 encabezados | {status} | {detail} |
| C6 | Escritura de fila de prueba | {status} | {detail} |
| C7 | Lectura y verificacion de integridad | {status} | {detail} |
| C8 | Eliminacion de pestana de prueba | {status} | {detail} |
| C9 | Permisos de cuenta: editor (no owner) | {status} | {detail} |

## 4. Importacion de Historicos

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Fuente de historicos identificada | {status} | {source_type} |
| C2 | Campos minimos validados | {status} | {detail} |
| C3 | Registros importados a `_Control` | {status} | {N} registros |
| C4 | Duplicados detectados | {status} | {N} duplicados |
| C5 | Consecutivos maximos calculados | {status} | Por grupo: {detail} |
| C6 | Sin corrupcion de datos existentes | {status} | {detail} |

## 5. Benchmark de Modelos (Qwen3-VL)

### 5.1 Configuracion

| Parametro | Valor |
|---|---|
| Modelo A | qwen3-vl:2b |
| Modelo B | qwen3-vl:4b |
| Total imagenes | {N} |
| Imagenes procesadas | {N} |
| Imagenes con error | {N} |
| Ground truth disponible | {si/no} |

### 5.2 Resultados por Modelo

| Metrica | 2B | 4B | Objetivo PRD §32 |
|---|---|---|---|
| JSON valido | {N}% | {N}% | >= 99% |
| Monto exacto | {N}% | {N}% | >= 95% |
| Fecha exacta | {N}% | {N}% | >= 90% |
| Banco correcto | {N}% | {N}% | >= 90% |
| Tipo correcto | {N}% | {N}% | >= 90% |
| Tiempo promedio | {N}s | {N}s | <= 5 min |
| RAM pico | {N} MB | {N} MB | < 16 GB |

### 5.3 Recomendacion

{Recommended model with justification. If neither meets all thresholds, document which thresholds failed and suggest alternatives.}

---

## Artefactos Generados

| Archivo | Tipo | Descripcion |
|---|---|---|
| `harness/evidence/fase0/benchmark-modelos.json` | report | Benchmark results in JSON |
| `harness/evidence/fase0/benchmark-modelos.md` | report | Benchmark results in Markdown |
| `harness/evidence/fase0/validacion-postgresql.json` | report | PostgreSQL validation JSON |
| `harness/evidence/fase0/validacion-postgresql.md` | report | PostgreSQL validation MD |
| `harness/evidence/fase0/validacion-sheets.json` | report | Sheets validation JSON |
| `harness/evidence/fase0/validacion-sheets.md` | report | Sheets validation MD |
| `harness/evidence/fase0/importacion-historicos.json` | report | Historical import JSON |
| `harness/evidence/fase0/importacion-historicos.md` | report | Historical import MD |
| `harness/evidence/fase0/validacion-secretos.json` | report | Secrets validation JSON |
| `harness/evidence/fase0/validacion-secretos.md` | report | Secrets validation MD |
| `scripts/validation/validate_postgresql.py` | script | PostgreSQL connectivity test |
| `scripts/validation/validate_sheets.py` | script | Google Sheets API test |
| `scripts/validation/import_historicos.py` | script | Historical data import |
| `scripts/validation/benchmark_modelos.py` | script | Model benchmark runner |

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

1. Obtener autorizacion GATE manual para Fase 0
2. Si Fase 0 aprobada, iniciar `skill-fase1-nucleo`
3. Configurar modelo recomendado como predeterminado en Ollama
4. Archivar scripts de validacion (no son necesarios en produccion)

---

## Precondiciones al Inicio

```json
{
  "branch": "arnes",
  "prd_version": "1.2",
  "fase0_status": "pending",
  "ejemplos_count": {N},
  "ollama_version": "{version}",
  "postgresql_accessible": {true/false},
  "google_credentials_path": "{masked_path}",
  "uv_version": "{version}"
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
