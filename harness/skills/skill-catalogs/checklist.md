# Checklist — skill-catalogs

## Pre-ejecución
- [ ] skill-web-ui completado (base templates, nav, roles)
- [ ] skill-database completado (modelos Category, Account, User)
- [ ] skill-authentication completado (get_current_user, hashing)
- [ ] Usuario admin (Ruben) creado con role='admin'
- [ ] Usuario estándar (Esme) creado con role='estandar'
- [ ] `uv sync --frozen` exitoso
- [ ] Branch `arnes` activa
- [ ] app/catalogs/ y app/users/ directorios existen

## Ejecución
- [ ] Paso 1: Modelos Category, Account, User verificados en models.py
- [ ] Paso 1: app/catalogs/repository.py con CRUD + soft delete + is_in_use
- [ ] Paso 1: app/users/repository.py con create, deactivate, reset_password, unlock
- [ ] Paso 2: app/api/catalogs.py con todas las rutas CRUD
- [ ] Paso 2: Rutas de categorías (GET list, POST create, PUT update, DELETE deactivate)
- [ ] Paso 2: Rutas de cuentas (mismo patrón)
- [ ] Paso 2: Rutas de usuarios (list, create, edit role, reset password, unlock, deactivate)
- [ ] Paso 2: Verificación is_in_use antes de operaciones de borrado
- [ ] Paso 3: templates/catalogs.html con tabs (Categorías, Cuentas, Usuarios)
- [ ] Paso 3: templates/partials/catalogs/categories.html con tabla + inline edit
- [ ] Paso 3: templates/partials/catalogs/accounts.html con tabla + inline edit
- [ ] Paso 3: templates/partials/catalogs/users.html con tabla + acciones
- [ ] Paso 3: Formularios de edición inline (category, account, user)
- [ ] Paso 4: Dependencia require_admin implementada
- [ ] Paso 4: Todas las rutas de catálogos protegidas con require_admin
- [ ] Paso 4: Esme recibe 403 en /catalogs/*
- [ ] Paso 4: Enlace de catálogos solo visible para admin en nav
- [ ] Paso 5: Soft delete: active=False, nunca borrado físico de entidades en uso
- [ ] Paso 5: Advertencia al desactivar entidad en uso: "en uso en {N} registros"
- [ ] Paso 5: No se puede desactivar al propio admin
- [ ] Paso 6: Endpoints GET /catalogs/categories/active y /accounts/active
- [ ] Paso 6: Dropdowns en formulario de gasto solo muestran activos
- [ ] Paso 6: Entidad desactivada muestra "(desactivado)" en dropdown seleccionado
- [ ] Paso 7: Tests unitarios pasan (>= 90% cobertura)
- [ ] Paso 7: Tests de integración pasan
- [ ] Paso 7: Tests E2E pasan
- [ ] Paso 8: Evidencia JSON generada
- [ ] Paso 8: Evidencia MD generada

## Post-ejecución
- [ ] Admin puede crear/editar/desactivar categorías
- [ ] Admin puede crear/editar/desactivar cuentas
- [ ] Admin puede crear/editar/desactivar/desbloquear usuarios
- [ ] No se puede desactivar el propio admin
- [ ] Categoría en uso → solo desactivación, con advertencia
- [ ] Edición inline con HTMX sin recarga de página
- [ ] Confirmación antes de desactivar/eliminar
- [ ] Validación de duplicados (código único)
- [ ] Nuevos usuarios forzados a cambiar contraseña
- [ ] Contraseñas hasheadas con Argon2id
- [ ] Esme no puede acceder a ninguna ruta de catálogos
- [ ] Cobertura >= 90%
- [ ] Sin secretos en código
- [ ] Lint, mypy, ruff pasan
