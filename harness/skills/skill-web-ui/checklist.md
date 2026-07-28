# Checklist — skill-web-ui

## Pre-ejecución
- [ ] Authentication skill completado (login endpoints, sesiones, Argon2id)
- [ ] Image extraction skill completado (Ollama produce JSON con confianza)
- [ ] FIFO queue skill completado (flujo EN_COLA → ANALIZANDO → LISTO/REQUIERE)
- [ ] Database skill completado (modelos SQLAlchemy accesibles)
- [ ] Folder monitor skill completado (thumbnails generados)
- [ ] FastAPI scaffold existe en `app/main.py`
- [ ] Jinja2 está configurado con `templates/` como directorio
- [ ] Carpeta `static/` existe
- [ ] `uv sync --frozen` exitoso
- [ ] Branch `arnes` activa

## Ejecución
- [ ] Paso 1: `static/css/style.css` creado con estilos base, status badges, confidence colors
- [ ] Paso 1: `templates/base.html` creado con header, nav, bloques
- [ ] Paso 1: `app/api/webui.py` creado con todas las rutas de vista
- [ ] Paso 2: `templates/login.html` creado, login funcional con Argon2id
- [ ] Paso 2: Bloqueo por intentos (5 intentos, 15 min) implementado
- [ ] Paso 2: Redirección post-login a dashboard
- [ ] Paso 3: `templates/dashboard.html` con polling `every 3s`
- [ ] Paso 3: `templates/partials/expense-table.html` parcial con columnas correctas
- [ ] Paso 3: Columna Owner visible solo para admin
- [ ] Paso 4: `templates/expense-viewer.html` con layout two-column
- [ ] Paso 4: `templates/partials/image-viewer.html` con zoom, rotate, fullscreen
- [ ] Paso 4: `templates/partials/expense-form.html` con 16 campos PRD Sección 11
- [ ] Paso 4: Sincronización precio_unitario = total
- [ ] Paso 4: Botón "Enviar" deshabilitado si faltan campos obligatorios
- [ ] Paso 5: `templates/partials/expense-status.html` con polling condicional
- [ ] Paso 5: Polling se detiene en estados terminales
- [ ] Paso 5: Preview de descripción final actualiza al cambiar grupo/descripción
- [ ] Paso 6: Filtro por owner para Esme en todas las queries
- [ ] Paso 6: Catálogos retornan 403 para Esme
- [ ] Paso 6: Admin puede ver/editar cualquier registro
- [ ] Paso 7: Placeholder para imagen no cargada
- [ ] Paso 7: Bloqueo optimista para ediciones concurrentes
- [ ] Paso 7: Formulario readonly hasta LISTO_PARA_REVISION
- [ ] Paso 7: Redirección a login en 401 durante HTMX
- [ ] Paso 8: Tests unitarios pasan (>= 90% cobertura)
- [ ] Paso 8: Tests de integración pasan
- [ ] Paso 8: Tests E2E pasan
- [ ] Paso 9: Evidencia JSON generada
- [ ] Paso 9: Evidencia MD generada

## Post-ejecución
- [ ] Todos los templates cargan sin errores Jinja2
- [ ] Login funciona con Ruben y Esme
- [ ] Dashboard muestra lista de gastos filtrada por rol
- [ ] Estados se actualizan cada 3s sin F5
- [ ] Polling se detiene en ENVIADO, DUPLICADO_EXACTO, ERROR_PROCESAMIENTO
- [ ] Visor de imagen: zoom, rotación, fullscreen funcionales
- [ ] Formulario: sincronización precio_unitario/total
- [ ] Botón enviar: bloqueado/desbloqueado según campos obligatorios
- [ ] Esme no ve catálogos ni gastos de Ruben
- [ ] Ruben ve todo
- [ ] Responsive: layout funciona en viewport < 768px
- [ ] No hay JS externo aparte de HTMX
- [ ] Cero secretos hardcodeados
- [ ] Cobertura >= 90%
- [ ] Lint, mypy, ruff pasan
