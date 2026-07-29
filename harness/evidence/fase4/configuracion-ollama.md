# Evidence Report — configuracion-ollama

> **Skill:** `skill-infrastructure` | **Fase:** `fase4`
> **Timestamp:** `2026-07-28T22:51:00` | **Estado:** PASADO

---

## Resumen Ejecutivo

Instalacion de Ollama y descarga del modelo multimodal Qwen3-VL:4b (3.3 GB) para la extraccion de datos de imagenes de tickets. Ollama corre como servicio systemd en localhost:11434. La VM no tiene GPU, por lo que la inferencia es CPU-only.

---

## Metricas

| Metrica | Valor |
|---|---|
| Modelo | qwen3-vl:4b |
| Tamano | 3.3 GB |
| Model ID | 1343d82ebee3 |
| Servicio | active (enabled) |
| GPU | CPU-only (sin NVIDIA/AMD) |

---

## Verificaciones

| # | Verificacion | Estado |
|---|---|---|
| C36 | Ollama instalado | PASADO |
| C37 | Servicio ollama running | PASADO |
| C38 | qwen3-vl:4b pulled | PASADO (3.3 GB) |
| C39 | ollama list confirma modelo | PASADO |
| C40 | Bound to localhost only | PASADO (default, sin OLLAMA_HOST override) |

---

## Puertos

| Puerto | Servicio | Acceso |
|---|---|---|
| 11434 | Ollama API | localhost only |

---

*Reporte generado por skill-infrastructure — Gastos IA v1.0*
