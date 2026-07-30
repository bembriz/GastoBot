# Evidencia: Diagnostico del Sistema

- **Skill:** skill-installer
- **Fase:** 4
- **Timestamp:** 2026-07-29T15:19:05Z
- **Status:** passed

## Resumen

Diagnostico completo del sistema generado sin secretos. Todos los componentes del sistema operativos.

## Checks

| ID | Descripcion | Status |
|----|------------|--------|
| DIAG-01 | VM specs (4 vCPU, 15GB, 58GB) | passed |
| DIAG-02 | Servicios activos (3/3) | passed |
| DIAG-03 | DB conectada | passed |
| DIAG-04 | Ollama qwen3-vl:4b | passed |
| DIAG-05 | SMB Ruben + Esme | passed |
| DIAG-06 | Permisos env 600 | passed |
| DIAG-07 | Sin secretos | passed |

## Especificaciones

| Componente | Valor |
|-----------|-------|
| CPU | 4 vcores |
| RAM | 15 GiB (14 GiB available) |
| Disco | 58 GB (43 GB free, 23%) |
| OS | Ubuntu 24.04.4 LTS |
| Kernel | 6.8.0-136-generic |
| Python | 3.12.3 |
| uv | 0.12.0 |
| FastAPI | 0.140.13 |
| Ollama | qwen3-vl:4b |
| PostgreSQL | 192.168.100.45:5432 |
| Caddy | HTTPS gastos.local |

## Servicios

| Servicio | Estado |
|----------|--------|
| gastos-ia | active (enabled) |
| caddy | active (enabled) |
| ollama | active (enabled) |

## Diagnostico JSON

Archivo completo: `scripts/diagnostics/diagnostic-2026-07-29.json`
