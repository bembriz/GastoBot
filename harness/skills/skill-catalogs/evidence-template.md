# Evidence Report — skill-catalogs

> **Skill:** `skill-catalogs`
> **Fase:** `fase2`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duración:** `{duration}`

---

## Resumen Ejecutivo

Implementación del sistema de catálogos para Gastos IA: CRUD de categorías, cuentas y usuarios con acceso exclusivo de administrador. Soft delete para entidades en uso, edición inline con HTMX, y gestión completa de usuarios (crear, desactivar, reset password, desbloquear). {summary}.

---

## Métricas

| Métrica | Valor |
|---|---|
| Entidades gestionadas | 3 (Categorías, Cuentas, Usuarios) |
| Rutas API creadas | {N} |
| Templates creados | {N} |
| Partial templates (HTMX) | {N} |
| Categorías creadas | {N} |
| Cuentas creadas | {N} |
| Usuarios gestionados | {N} |
| Tests unitarios | {N}/{N} |
| Tests de integración | {N}/{N} |
| Tests E2E | {N}/{N} |
| Cobertura de código | {N}% |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | skill-web-ui completado | {status} | {detail} |
| C2 | skill-database completado | {status} | {detail} |
| C3 | skill-authentication completado | {status} | {detail} |
| C4 | Admin user (Ruben) existe | {status} | {detail} |
| C5 | Standard user (Esme) existe | {status} | {detail} |

### Ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Modelos Category, Account, User verificados | {status} | {detail} |
| C2 | CategoryRepository con soft delete e is_in_use | {status} | {detail} |
| C3 | AccountRepository con soft delete e is_in_use | {status} | {detail} |
| C4 | UserRepository con create/deactivate/reset/unlock | {status} | {detail} |
| C5 | require_admin dependency | {status} | {detail} |
| C6 | Ruta GET /catalogs (página principal) | {status} | {detail} |
| C7 | CRUD categorías: create | {status} | {detail} |
| C8 | CRUD categorías: read (list) | {status} | {detail} |
| C9 | CRUD categorías: update inline | {status} | {detail} |
| C10 | CRUD categorías: deactivate (soft delete) | {status} | {detail} |
| C11 | Advertencia al desactivar entidad en uso | {status} | {detail} |
| C12 | CRUD cuentas: create | {status} | {detail} |
| C13 | CRUD cuentas: read (list) | {status} | {detail} |
| C14 | CRUD cuentas: update inline | {status} | {detail} |
| C15 | CRUD cuentas: deactivate (soft delete) | {status} | {detail} |
| C16 | Gestión usuarios: listar | {status} | {detail} |
| C17 | Gestión usuarios: crear (hash Argon2id) | {status} | {detail} |
| C18 | Gestión usuarios: editar rol | {status} | {detail} |
| C19 | Gestión usuarios: reset password | {status} | {detail} |
| C20 | Gestión usuarios: desbloquear | {status} | {detail} |
| C21 | Gestión usuarios: desactivar | {status} | {detail} |
| C22 | No desactivar propio admin | {status} | {detail} |
| C23 | 403 para Esme en /catalogs/* | {status} | {detail} |
| C24 | Nav: catálogos solo admin | {status} | {detail} |
| C25 | Active-only endpoints para dropdowns | {status} | {detail} |
| C26 | Edición inline HTMX funciona | {status} | {detail} |
| C27 | Validación de duplicados | {status} | {detail} |
| C28 | Must change password en nuevos usuarios | {status} | {detail} |
| C29 | Tabla vacía muestra mensaje y botón crear | {status} | {detail} |
| C30 | Tests unitarios >= 90% | {status} | {detail} |

### Post-ejecución

| # | Verificación | Estado | Detalle |
|---|---|---|---|
| C1 | Admin puede gestionar categorías, cuentas y usuarios | {status} | {detail} |
| C2 | Esme no accede a catálogos | {status} | {detail} |
| C3 | Soft delete preserva integridad referencial | {status} | {detail} |
| C4 | Sin secretos | {status} | {detail} |
| C5 | Lint/mypy/ruff pasan | {status} | {detail} |

---

## Artefactos Generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `app/catalogs/repository.py` | source | Repositorio de catálogos |
| `app/users/repository.py` | source | Repositorio de usuarios |
| `app/api/catalogs.py` | source | Rutas API de catálogos |
| `app/auth/dependencies.py` | source | Dependencia require_admin |
| `templates/catalogs.html` | template | Página principal de catálogos |
| `templates/partials/catalogs/categories.html` | template | Tabla de categorías |
| `templates/partials/catalogs/accounts.html` | template | Tabla de cuentas |
| `templates/partials/catalogs/users.html` | template | Tabla de usuarios |
| `templates/partials/catalogs/*-edit-form.html` | template | Formularios de edición inline |
| `tests/unit/test_catalogs.py` | test | Tests unitarios |
| `tests/integration/test_catalogs.py` | test | Tests de integración |

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

1. Completar `skill-history` para historial de gastos
2. Verificar integración con dropdowns en formulario de gasto
3. Preparar sincronización con Google Sheets (_Categorias, _Cuentas) en Fase 3

---

## Precondiciones al Inicio

```json
{
  "web_ui_skill": "completed",
  "database_skill": "completed",
  "authentication_skill": "completed",
  "admin_user_exists": true,
  "standard_user_exists": true,
  "catalogs_dir": "exists",
  "users_dir": "exists"
}
```

---

*Reporte generado automáticamente por el arnés Gastos IA v1.0*
