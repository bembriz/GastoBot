# Evidence Report — E2E Tests

> **Skill:** `skill-e2e-tests`  
> **Fase:** `{phase}`  
> **Timestamp:** `{iso8601}`  
> **Estado:** `[PASADO | FALLADO]`  
> **Duración:** `{duration}`  

---

## Resumen Ejecutivo

{One-paragraph summary: E2E flows tested with Playwright, browsers used, flujos completos y edge cases verificados.}

---

## Métricas

| Métrica | Valor |
|---|---|
| Flujos totales | {N} |
| Flujos pasados | {N} |
| Flujos fallidos | {N} |
| Screenshots generados | {N} |
| Tiempo total | {N}s |
| Navegadores | Chromium |

---

## Flujos Ejecutados

| # | Flujo | Usuario | Estado | Tiempo | Screenshot |
|---|---|---|---|---|---|
| 1 | Login exitoso → dashboard | Ruben | {status} | {N}s | {path} |
| 2 | Login exitoso → dashboard | Esme | {status} | {N}s | {path} |
| 3 | Login fallido → bloqueo (5 intentos) | Ruben | {status} | {N}s | {path} |
| 4 | Procesar imagen → revisar → enviar | Ruben | {status} | {N}s | {path} |
| 5 | Procesar imagen → revisar → enviar | Esme | {status} | {N}s | {path} |
| 6 | Cola FIFO: 5 imágenes simultáneas | Ruben | {status} | {N}s | {path} |
| 7 | Solo una en ANALIZANDO | Ruben | {status} | {N}s | {path} |
| 8 | Duplicado exacto → bloqueado | Ruben | {status} | {N}s | {path} |
| 9 | Operación offline → PENDIENTE_DE_ENVIO | Ruben | {status} | {N}s | {path} |
| 10 | Recuperación post-offline → enviar | Ruben | {status} | {N}s | {path} |
| 11 | CRUD catálogos (categorías) | Ruben | {status} | {N}s | {path} |
| 12 | CRUD catálogos (cuentas) | Ruben | {status} | {N}s | {path} |
| 13 | Catálogos bloqueados para Esme | Esme | {status} | {N}s | {path} |
| 14 | Historial: búsqueda y filtros | Ruben | {status} | {N}s | {path} |
| 15 | Historial: editar → actualizar Sheets | Ruben | {status} | {N}s | {path} |
| 16 | HTMX polling: transiciones visibles | Ruben | {status} | {N}s | {path} |
| 17 | HTMX polling: dos navegadores simultáneos | Ambos | {status} | {N}s | {path} |
| 18 | Formulario: sincronización precio↔total | Ruben | {status} | {N}s | {path} |
| 19 | Formulario: botón bloqueado sin campos req. | Ruben | {status} | {N}s | {path} |
| 20 | Cambio de mes: mover registro | Ruben | {status} | {N}s | {path} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Playwright instalado | {status} | {detail} |
| C2 | Navegadores Chromium instalados | {status} | {detail} |
| C3 | App corriendo en localhost | {status} | {detail} |
| C4 | Base de datos limpia de test | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | 0 flujos fallidos | {status} | {N} fallidos |
| C2 | Screenshots generados para todos los flujos | {status} | {N}/{N} |
| C3 | Criterios de aceptación verificados | {status} | {N}/39 |

---

## Criterios de Aceptación Verificados

| # | Criterio (PRD §33) | Flujo asociado | Estado |
|---|---|---|---|
| 1 | VM y servicios inician automáticamente | {N} | {status} |
| 2 | Accesible desde ambos equipos | {N} | {status} |
| ... | ... | ... | ... |
| 39 | No commits sin autorización | {N} | {status} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `tests/e2e/test_*.py` | Source | Tests E2E |
| `tests/e2e/screenshots/*.png` | Evidence | Screenshots por flujo |
| `tests/e2e/videos/*.webm` | Evidence | Grabaciones de sesión |

---

## Errores

| Código | Mensaje |
|---|---|
| {code} | {message} |

---

## Próximos Pasos

1. Ejecutar skill-uat-instructions
2. Corregir flujos fallidos

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
