# Progress Tracking — Gastos IA

> Última actualización: 2026-07-28T13:00:00  

---

## Resumen Global

| Fase | Estado | Progreso | ETA | ETA restante |
|---|---|---|---|---|
| Fase 0 — Prueba Técnica | **in_progress** | 80% | 8h | ~1.5h (benchmark en VM) |
| Fase 1 — Núcleo | pending | 0% | 20h | — |
| Fase 2 — Interfaz | pending | 0% | 16h | — |
| Fase 3 — Google Sheets | pending | 0% | 12h | — |
| Fase 4 — Instalador | pending | 0% | 10h | — |
| Fase 5 — Aceptación | pending | 0% | 8h | — |

---

## Fase 0 — Prueba Técnica  

**Estado:** in_progress | **Progreso:** 80% (4/5 pasos)

| # | Tarea | Estado | Checks | Detalle |
|---|---|---|---|---|
| 1 | Validación de secretos | **completed** | 19/19 | `.env.example` creado, `.envrc` configurado |
| 2 | Validación de PostgreSQL | **completed** | 7/7 | BD `gastos_ia` + usuario `gastos_app` en 192.168.100.45 |
| 3 | Validación de Google Sheets | **completed** | 8/8 | Autenticado, 10 pestañas, `_Control` creada |
| 4 | Importación de históricos | **completed** | 618 registros | 10 grupos con consecutivos máximos |
| 5 | Benchmark Qwen3-VL | **deferred** | — | Diferido a VM (Fase 4), script listo |

### Consecutivos por grupo (para Fase 1)

| Grupo | Próximo |
|---|---|
| BORAMAR | 3 |
| BUNG | 4 |
| ESTRADOS | 5 |
| OP | 39 |
| PISTANESS | 5 |
| PSAV | 13 |
| STRINGLIGHTS | 14 |
| VAL | 16 |
| VALC | 4 |
| XCARET | 10 |

### Artefactos

| Evidencia | Estado |
|---|---|
| `validacion-secretos.{json,md}` | Generado (19/19) |
| `validacion-postgresql.{json,md}` | Generado (7/7) |
| `validacion-sheets.{json,md}` | Generado (8/8) |
| `importacion-historicos.{json,md}` | Generado (618 registros) |
| `benchmark-modelos.{json,md}` | Deferred (VM) |

### Scripts

| Script | Estado |
|---|---|
| `validate_secrets.py` | Ejecutado |
| `validate_postgresql.py` | Ejecutado |
| `validate_sheets.py` | Ejecutado |
| `import_historicos.py` | Ejecutado (via inline script) |
| `benchmark_modelos.py` | Listo para VM |
