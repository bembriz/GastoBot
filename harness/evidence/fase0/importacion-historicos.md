# Evidence Report — Importación de Históricos

> **Skill:** `skill-fase0-tecnica`  
> **Fase:** `fase0`  
> **Timestamp:** `2026-07-28T13:00:00Z`  
> **Estado:** PASADO  
> **Duración:** 45s  

---

## Resumen Ejecutivo

618 registros históricos importados exitosamente desde 7 pestañas mensuales (Enero-Julio 2026) a la hoja `_Control`. Se detectaron 10 grupos con sus secuencias de consecutivos. El sistema anterior reiniciaba consecutivos por mes; ahora son globales por grupo. Los próximos registros continuarán desde el consecutivo máximo + 1.

---

## Métricas

| Métrica | Valor |
|---|---|
| Registros importados | 618 |
| Duplicados descartados | 100 (descripción exacta) |
| Grupos detectados | 10 |
| Pestañas leídas | 7 |
| Columnas por registro | 16 |

---

## Grupos y Consecutivos

| Grupo | Máximo histórico | Próximo consecutivo |
|---|---|---|
| BORAMAR | 2 | 3 |
| BUNG | 3 | 4 |
| ESTRADOS | 4 | 5 |
| OP | 38 | 39 |
| PISTANESS | 4 | 5 |
| PSAV | 12 | 13 |
| STRINGLIGHTS | 13 | 14 |
| VAL | 15 | 16 |
| VALC | 3 | 4 |
| XCARET | 9 | 10 |

---

## Verificaciones

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Lectura de pestañas | PASADO | 7 pestañas mensuales |
| C2 | Parseo de descripciones | PASADO | Formato `GRUPO-YYMMDD -N - DESCRIPCION` |
| C3 | Deduplicación por descripción | PASADO | 100 duplicados exactos descartados |
| C4 | Cálculo de consecutivos | PASADO | 10 grupos con secuencias completas |
| C5 | Escritura en `_Control` | PASADO | 618 registros × 16 columnas |

---

## Advertencias

- El sistema anterior reiniciaba consecutivos por mes. Los registros importados preservan sus números originales.
- Algunos grupos (OP, VAL, PSAV) tienen muchos registros en diferentes meses con el mismo consecutivo. Solo se importó uno de cada conjunto duplicado por descripción exacta.

---

## Próximos Pasos

1. Benchmark de modelos Qwen3-VL (requiere Ollama en VM)
2. Cierre de Fase 0

---

*Reporte generado por el arnés Gastos IA v1.0*
