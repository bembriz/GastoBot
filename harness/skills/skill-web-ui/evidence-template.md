# Evidence Report — skill-web-ui

> **Skill:** `skill-web-ui`
> **Fase:** `fase2`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

Implementación de la interfaz web completa para Gastos IA: login, dashboard con polling HTMX, visor de imágenes con zoom/rotate/fullscreen, y formulario de revisión con 16 campos alineados al PRD Sección 11. {summary of what was built, what passed, any issues}.

---

## Métricas

| Métrica | Valor |
|---|---|
| Templates Jinja2 creados | {N} |
| Partial templates (HTMX) | {N} |
| Rutas de vista (GET/POST) | {N} |
| Páginas principales | {N} |
| Tests unitarios | {N}/{N} |
| Tests de integración | {N}/{N} |
| Tests E2E | {N}/{N} |
| Cobertura de código | {N}% |
| Errores | {N} |
| Advertencias | {N} |

### Métricas de Interfaz

| Métrica | Valor |
|---|---|
| Tiempo de carga dashboard (cold) | {N}ms |
| Tiempo de carga visor (cold) | {N}ms |
| Tamaño de respuesta polling | {N}KB |
| Latencia polling (promedio) | {N}ms |
| Transiciones de estado visibles | EN_COLA→ANALIZANDO→LISTO_PARA_REVISION |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Authentication skill completado | {status} | {detail} |
| C2 | Image extraction skill completado | {status} | {detail} |
| C3 | FIFO queue skill completado | {status} | {detail} |
| C4 | Database skill completado | {status} | {detail} |
| C5 | Folder monitor skill completado | {status} | {detail} |
| C6 | FastAPI + Jinja2 configurado | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | static/css/style.css creado | {status} | {detail} |
| C2 | templates/base.html con layout base | {status} | {detail} |
| C3 | app/api/webui.py con rutas | {status} | {detail} |
| C4 | Login funcional (Ruben) | {status} | {detail} |
| C5 | Login funcional (Esme) | {status} | {detail} |
| C6 | Bloqueo tras 5 intentos fallidos | {status} | {detail} |
| C7 | Dashboard con lista de gastos | {status} | {detail} |
| C8 | HTMX Polling cada 3s en dashboard | {status} | {detail} |
| C9 | Table columns: Thumbnail, File, Date, Amount, Bank, Status, Warnings, Owner(admin) | {status} | {detail} |
| C10 | Status badges con colores correctos | {status} | {detail} |
| C11 | Warning indicators para baja confianza | {status} | {detail} |
| C12 | Visor de gasto individual | {status} | {detail} |
| C13 | Image viewer: zoom in/out | {status} | {detail} |
| C14 | Image viewer: rotate 90deg | {status} | {detail} |
| C15 | Image viewer: fullscreen | {status} | {detail} |
| C16 | Formulario con 16 campos PRD Sección 11 | {status} | {detail} |
| C17 | Sincronización precio_unitario ↔ total | {status} | {detail} |
| C18 | Botón enviar bloqueado sin campos obligatorios | {status} | {detail} |
| C19 | Confidence indicators en campos extraídos | {status} | {detail} |
| C20 | Polling se detiene en estados terminales | {status} | {detail} |
| C21 | Polling condicional en expense-status | {status} | {detail} |
| C22 | Preview descripción final (Grupo-Consecutivo-Desc) | {status} | {detail} |
| C23 | Filtro por owner para Esme | {status} | {detail} |
| C24 | Admin ve todos los registros | {status} | {detail} |
| C25 | Esme recibe 403 en /catalogs/* | {status} | {detail} |
| C26 | Placeholder imagen no cargada | {status} | {detail} |
| C27 | Bloqueo optimista (concurrent edits) | {status} | {detail} |
| C28 | Redirección a login en sesión expirada | {status} | {detail} |
| C29 | Layout responsive (mobile < 768px) | {status} | {detail} |
| C30 | No JS externo aparte de HTMX | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Todos los templates cargan sin errores | {status} | {detail} |
| C2 | Tests unitarios >= 90% cobertura | {status} | {detail} |
| C3 | Tests de integración pasan | {status} | {detail} |
| C4 | Tests E2E pasan | {status} | {detail} |
| C5 | Lint (ruff check) pasa | {status} | {detail} |
| C6 | Tipos (mypy) pasan | {status} | {detail} |
| C7 | Sin secretos expuestos | {status} | {detail} |
| C8 | Evidencia JSON y MD generadas | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `templates/base.html` | template | Layout base Jinja2 con nav y header |
| `templates/login.html` | template | Página de login |
| `templates/dashboard.html` | template | Dashboard principal con polling |
| `templates/expense-viewer.html` | template | Visor individual de gasto |
| `templates/partials/expense-table.html` | template | Parcial HTMX de tabla de gastos |
| `templates/partials/expense-status.html` | template | Parcial HTMX de fila de estado |
| `templates/partials/expense-form.html` | template | Parcial HTMX del formulario |
| `templates/partials/image-viewer.html` | template | Parcial HTMX visor de imagen |
| `static/css/style.css` | stylesheet | Estilos de la aplicación |
| `app/api/webui.py` | source | Rutas de vista |
| `tests/unit/test_webui.py` | test | Tests unitarios de interfaz |
| `tests/integration/test_webui.py` | test | Tests de integración |
| `tests/e2e/test_webui.py` | test | Tests E2E |

---

## Errores (si los hay)

| Código | Mensaje |
|---|---|
| {code} | {message} |

---

## Advertencias (si las hay)

- {warning}

---

## Próximos Pasos

1. Completar `skill-catalogs` para CRUD de categorías, cuentas y usuarios
2. Verificar integración con Google Sheets en Fase 3
3. Validar polling con imágenes reales procesándose

---

## Precondiciones al Inicio

```json
{
  "authentication_skill": "completed",
  "image_extraction_skill": "completed",
  "fifo_queue_skill": "completed",
  "database_skill": "completed",
  "folder_monitor_skill": "completed",
  "fastapi_scaffold": true,
  "jinja2_configured": true,
  "templates_dir": "exists",
  "static_dir": "exists"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
