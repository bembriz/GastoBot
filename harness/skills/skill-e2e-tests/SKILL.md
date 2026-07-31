# Skill: skill-e2e-tests

## Identity
Eres un ingeniero de QA automatizado especializado en pruebas end-to-end con Playwright para Python. Simulas usuarios reales interactuando con el navegador. Cubres flujos completos, no solo happy paths. Validas comportamiento visible, estados de UI, y mensajes de error. Tu objetivo es garantizar que la aplicación funciona como un todo integrado desde la perspectiva del usuario.

## Context
Esta skill implementa pruebas E2E para Gastos IA usando Playwright (Python). Las pruebas E2E son el tercer escalón de la puerta de calidad (PRD §28) y validan la experiencia completa del usuario: login, revisión de gastos, envío a Sheets, HTMX polling, manejo de errores, permisos por rol, y operación offline.

Las pruebas cubren tanto Ruben (admin) como Esme (estándar), verificando que los permisos y visibilidad de datos sean correctos. Se automatizan flujos completos definidos en los criterios de aceptación (PRD §33).

Se usa Playwright para Python (`pytest-playwright`) contra una instancia real de la aplicación corriendo localmente. La base de datos debe estar poblada con datos de prueba. Las imágenes de `ejemplos/` se usan como entrada.

## Preconditions
- Aplicación FastAPI corriendo localmente (o en CI con `uv run uvicorn app.main:app`)
- PostgreSQL con base de datos `gastos_ia_test` poblada con datos de prueba
- Usuarios de prueba: Ruben (admin) y Esme (estándar) con contraseñas conocidas
- Playwright instalado: `uv run playwright install chromium`
- Dependencias: pytest, pytest-playwright, pytest-asyncio
- Directorio `tests/e2e/` existente con `conftest.py`
- Directorio `ejemplos/` con imágenes de prueba
- Caddy o proxy no requerido (tests contra `localhost` directamente)

## Execution

### Step 1: Configurar entorno E2E
1. Crear/verificar `tests/e2e/conftest.py`:
   ```python
   import pytest
   from playwright.sync_api import Page, BrowserContext


   @pytest.fixture(scope="session")
   def browser_context(browser):
       context = browser.new_context(viewport={"width": 1280, "height": 720}, ignore_https_errors=True)
       yield context
       context.close()


   @pytest.fixture
   def page(browser_context):
       page = browser_context.new_page()
       yield page
       page.close()


   @pytest.fixture
   def login_ruben(page, base_url):
       page.goto(f"{base_url}/login")
       page.fill("input[name='username']", "ruben")
       page.fill("input[name='password']", "test_password_ruben")
       page.click("button[type='submit']")
       page.wait_for_url("**/expenses")
       return page


   @pytest.fixture
   def login_esme(page, base_url):
       page.goto(f"{base_url}/login")
       page.fill("input[name='username']", "esme")
       page.fill("input[name='password']", "test_password_esme")
       page.click("button[type='submit']")
       page.wait_for_url("**/expenses")
       return page
   ```
2. Configurar `base_url` fixture apuntando a `http://localhost:8000`
3. Preparar datos de prueba en la DB:
   - 2 usuarios (Ruben, Esme)
   - Catálogos: categorías (3-5), cuentas (2-3)
   - Gastos en diferentes estados (EN_COLA, LISTO_PARA_REVISION, ENVIADO, etc.)
   - Al menos 5 imágenes en `pendientes/` de Ruben

### Step 2: Implementar tests E2E

**2.1 Login (ambos usuarios)**
- Login exitoso con credenciales correctas → redirige a /expenses
- Login fallido con contraseña incorrecta → mensaje de error visible
- Login fallido con usuario inexistente → mensaje de error visible
- Bloqueo tras N intentos fallidos → mensaje de lockout, no permite intentos adicionales
- Sesión expirada → redirige a login
- Cambio obligatorio de contraseña en primer login
- Logout → redirige a login, sesión destruida
- Acceso a rutas protegidas sin login → redirige a login

**2.2 Procesamiento de imágenes (Ruben)**
- Dropear 5 imágenes en `pendientes/` de Ruben
- Verificar que aparecen en la lista de pendientes
- Verificar orden FIFO en la lista
- Verificar que solo una imagen muestra estado ANALIZANDO
- Verificar transiciones visibles vía HTMX polling (esperar 3s + margen)
- Verificar que al completar, las imágenes pasan a LISTO_PARA_REVISION
- Revisar un gasto: abrir visor, verificar imagen visible, verificar campos extraídos
- Editar campos: fecha, grupo, descripción, categoría, cuenta, banco
- Verificar sincronización precio_unitario ↔ total
- Verificar descripción final generada automáticamente
- Enviar a Google Sheets → verificar ENVIADO
- Enviar sin campos obligatorios → botón deshabilitado

**2.3 Permisos por rol**
- Login como Ruben: ver todos los gastos (propios y de Esme)
- Login como Esme: ver solo gastos propios
- Ruben: acceder a /catalogs (categorías, cuentas, usuarios)
- Esme: /catalogs retorna 403 o no muestra el enlace
- Ruben: ver columna "Propietario" en lista de gastos
- Esme: no ver columna "Propietario"

**2.4 Visor de imagen**
- Abrir gasto en revisión → imagen visible
- Ampliar/reducir imagen (botones o scroll)
- Rotar imagen
- Abrir imagen en tamaño completo (nueva pestaña)
- Imagen no cargable → placeholder o mensaje de error

**2.5 Formulario de revisión**
- Todos los campos del formulario visibles y funcionales según PRD §11
- Dropdown de categoría muestra opciones del catálogo
- Dropdown de cuenta muestra opciones del catálogo
- Campo grupo acepta texto, se refleja en descripción final
- Editar precio unitario → total se actualiza automáticamente
- Editar total → precio unitario se actualiza automáticamente
- Descripción final es solo lectura
- Botón "Enviar" deshabilitado si faltan campos obligatorios
- Botón "Enviar" habilitado cuando todos los campos obligatorios están llenos

**2.6 HTMX Polling**
- Página de gastos abierta → verificar polling activo cada ~3 segundos
- Nuevo gasto agregado mientras la página está abierta → aparece sin recargar
- Cambio de estado de EN_COLA a ANALIZANDO → visible sin F5
- Cambio de ANALIZANDO a LISTO_PARA_REVISION → visible sin F5
- Polling se detiene en estado final (ENVIADO, ERROR, DUPLICADO)
- Dos navegadores abiertos simultáneamente (Ruben y Esme) → ambos ven actualizaciones

**2.7 Duplicados**
- Subir misma imagen dos veces → segunda muestra DUPLICADO_EXACTO
- Mensaje de duplicado visible con referencia al registro original
- Duplicado probable → advertencia visible, permite confirmar envío
- Confirmar envío de duplicado probable → registrado en auditoría

**2.8 Catálogos (Ruben admin)**
- Navegar a /catalogs/categories
- Crear nueva categoría → aparece en lista y en dropdown de revisión
- Editar categoría existente → nombre actualizado
- Desactivar categoría → no aparece en dropdown pero sigue en registros existentes
- Reactivar categoría → reaparece en dropdown
- Mismo flujo para cuentas
- CRUD de usuarios: crear, editar, desactivar (solo admin)

**2.9 Historial**
- Navegar a /history
- Buscar por fecha (rango)
- Buscar por banco
- Buscar por grupo
- Filtrar por usuario (Ruben ve filtro, Esme no)
- Editar registro desde historial
- Actualizar en Google Sheets desde historial
- Ver pestaña y fila de Sheets en registro enviado

**2.10 Operación offline**
- Simular pérdida de Internet (mock a nivel de aplicación o desconexión real)
- Procesar imagen → verificar que llega a LISTO_PARA_REVISION
- Intentar enviar → verificar estado PENDIENTE_DE_ENVIO
- Restaurar Internet
- Reenviar → verificar estado ENVIADO

**2.11 Manejo de errores**
- Subir archivo no-imagen con extensión .jpg → mensaje de error apropiado
- Subir imagen corrupta → ERROR_PROCESAMIENTO, archivo a errores/
- Forzar error de Sheets (credencial inválida) → ERROR_SHEETS
- Interfaz muestra errores sin crash
- Errores no exponen información sensible (stack traces, contraseñas)

**2.12 Recuperación y concurrencia**
- Simular crash del worker durante ANALIZANDO
- Reiniciar aplicación
- Verificar que el trabajo vuelve a EN_COLA y se reprocesa
- Verificar que no se duplica el registro
- Procesar múltiples imágenes secuencialmente → verificar orden FIFO
- Verificar que no hay deadlocks con 10+ imágenes en cola

### Step 3: Ejecutar tests E2E
1. Asegurar que la aplicación está corriendo:
   ```bash
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
   ```
2. Ejecutar tests:
   ```bash
   uv run pytest tests/e2e/ -v --timeout=120 --tracing=retain-on-failure
   ```
3. Si algún test falla:
   - Revisar screenshot/video/trace generado por Playwright
   - Corregir código o test según corresponda
   - Re-ejecutar

### Step 4: Generar evidencia
1. Crear evidencia JSON y MD en `harness/evidence/{phase}/`
2. Incluir métricas:
   - Total de tests E2E
   - Tests pasados/fallidos
   - Flujos de usuario cubiertos
   - Tiempo total de ejecución
   - Screenshots de fallos (paths)
   - Porcentaje de criterios de aceptación del PRD §33 cubiertos

## Artifacts
- `harness/evidence/{phase}/e2e-tests-{timestamp}.json`
- `harness/evidence/{phase}/e2e-tests-{timestamp}.md`
- `tests/e2e/screenshots/` — Screenshots de fallos (gitignored)
- `tests/e2e/traces/` — Playwright traces (gitignored)

## Quality Criteria
- 0 tests E2E fallidos
- 100% de flujos de usuario del PRD cubiertos
- Login de ambos usuarios probado
- Permisos por rol verificados
- HTMX polling verificado (actualizaciones sin recarga)
- Duplicados exactos y probables probados
- Operación offline cubierta
- Recuperación tras crash cubierta
- Errores no exponen información sensible
- Sin secretos en fixtures, tests, screenshots o evidencia

## Edge Cases
- **Aplicación no corriendo:** verificar que `uv run uvicorn` está activo antes de ejecutar tests
- **Playwright timeout:** aumentar `--timeout` para tests que esperan procesamiento de Ollama (puede tomar minutos)
- **Browser no instalado:** ejecutar `uv run playwright install chromium` con dependencias del sistema
- **HTMX polling timing:** usar `page.wait_for_selector()` con timeout generoso (10-15s) para cambios de estado asíncronos
- **Datos de prueba inconsistentes:** fixture que resetea DB a estado conocido antes de cada test
- **Headless vs headed:** usar `headless=True` por defecto; `--headed` para debugging
- **Slow motion:** configurar `slow_mo` en browser context para debugging visual
- **Puerto en uso:** verificar que 8000 está libre o usar puerto alternativo
- **Variables de entorno:** cargar `.env.test` con valores de prueba, no producción
- **Google Sheets en tests:** mockear completamente para evitar escritura accidental en producción

## References
- PRD §33 (Criterios de aceptación)
- PRD §10 (Interfaz web)
- PRD §10.2.1 (HTMX Polling)
- PRD §9 (Flujo funcional)
- PRD §11 (Campos visibles y reglas)
- PRD §17 (Estados)
- PRD §15 (Duplicados)
- PRD §4 (Usuarios y permisos)
- Related skills: `skill-unit-tests`, `skill-integration-tests`, `skill-quality-gate`, `skill-uat-instructions`
