# Checklist — skill-e2e-tests

## Pre-ejecución
- [ ] Aplicación FastAPI corriendo en `localhost:8000`
- [ ] Base de datos de prueba poblada (usuarios, catálogos, gastos)
- [ ] Playwright y navegador Chromium instalados
- [ ] `tests/e2e/conftest.py` con fixtures de login para ambos usuarios
- [ ] Directorio `ejemplos/` con imágenes de prueba accesibles
- [ ] Google Sheets mockeado (no escribir en producción)
- [ ] Variables de entorno de prueba configuradas (`.env.test`)
- [ ] Screenshots y traces directories creados (gitignored)

## Ejecución
- [ ] Login Ruben: credenciales correctas → redirect a /expenses
- [ ] Login Esme: credenciales correctas → redirect a /expenses
- [ ] Login fallido: contraseña incorrecta → mensaje de error
- [ ] Login fallido: usuario inexistente → mensaje de error
- [ ] Bloqueo tras N intentos: lockout visible, no más intentos
- [ ] Sesión expirada: redirect a login
- [ ] Cambio de contraseña inicial obligatorio
- [ ] Logout: redirect a login
- [ ] Rutas protegidas sin login: redirect a login
- [ ] Procesamiento: 5 imágenes → orden FIFO verificado
- [ ] Procesamiento: solo una imagen en ANALIZANDO a la vez
- [ ] HTMX polling: transiciones visibles sin F5 (EN_COLA→ANALIZANDO→LISTO)
- [ ] Visor: imagen visible, zoom, rotar, tamaño completo
- [ ] Formulario: todos los campos funcionan
- [ ] Formulario: sincronización precio_unitario ↔ total
- [ ] Formulario: descripción final generada automáticamente
- [ ] Formulario: botón deshabilitado si faltan campos
- [ ] Permisos Ruben: ver todos los gastos, acceder catálogos
- [ ] Permisos Esme: ver solo gastos propios, sin acceso a catálogos
- [ ] Duplicado exacto: segunda copia → DUPLICADO_EXACTO
- [ ] Duplicado probable: advertencia, permite confirmar
- [ ] Catálogos CRUD (Ruben): crear, editar, desactivar, reactivar
- [ ] Historial: búsqueda, filtros, edición, actualizar Sheets
- [ ] Offline: imagen procesada offline → PENDIENTE_DE_ENVIO
- [ ] Offline: reconectar → envío exitoso
- [ ] Error handling: imagen corrupta → ERROR_PROCESAMIENTO
- [ ] Error handling: archivo no-imagen → mensaje apropiado
- [ ] Error handling: no exponer secretos/stacktraces
- [ ] Recuperación: crash durante ANALIZANDO → vuelve a EN_COLA
- [ ] Recuperación: sin duplicados tras reinicio
- [ ] Concurrencia: 10+ imágenes en cola sin deadlocks

## Post-ejecución
- [ ] 0 tests E2E fallidos
- [ ] Screenshots de fallos revisados y guardados
- [ ] Playwright traces de fallos guardados
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra schema
- [ ] Métricas documentadas: tests pasados, flujos cubiertos, tiempo total
- [ ] Porcentaje de criterios de aceptación PRD §33 cubiertos documentado
- [ ] Ningún secreto en fixtures, tests, screenshots, traces o evidencia
- [ ] Datos de prueba no persisten en DB de producción
