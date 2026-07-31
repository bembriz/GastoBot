# Evidence Report — recuperacion-reinicio

> **Skill:** `skill-fase5-aceptacion`  
> **Fase:** `fase5`  
> **Timestamp:** `2026-07-30T05:30:00Z`  
> **Estado:** `PARCIAL`  

---

## Resumen Ejecutivo

La logica de recuperacion esta implementada (recover_stale_jobs en queue.py) y verificada via tests unitarios. El mecanismo detecta trabajos en estado ANALIZANDO con timestamps antiguos y los restaura a EN_COLA. Las pruebas completas de kill/reboot/restart requieren acceso a la VM GastosIA.

---

## Metricas

| Metrica | Valor |
|---|---|
| Criterios verificados | 2 |
| Criterios pendientes | 4 |
| Tests unitarios recovery | 4 |
| Errores | 0 |
| Advertencias | 1 |

---

## Verificaciones

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Criterio 12: Queue survive restart | pasado | recover_stale_jobs: ANALIZANDO -> EN_COLA |
| C2 | Criterio 33: Restart no pierde estado | pasado | PostgreSQL persistencia; estados verificados |
| C3 | Kill worker mid-processing | pendiente | Requiere VM |
| C4 | Full VM reboot | pendiente | Requiere VM |
| C5 | PostgreSQL restart | pendiente | Requiere acceso servidor |
| C6 | Rapid restarts (3x) | pendiente | Requiere VM |

---

## Advertencias

- Pruebas de recuperacion requieren acceso a la VM GastosIA (192.168.100.75)

---

## Proximos Pasos

1. SSH a VM: `ssh gastos-admin@192.168.100.75`
2. Kill worker: `sudo systemctl stop gastos-ia`
3. Verificar ANALIZANDO -> EN_COLA en PostgreSQL
4. Reboot: `sudo reboot` y verificar servicios + cola intacta

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
