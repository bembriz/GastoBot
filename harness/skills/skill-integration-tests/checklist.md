# Checklist — skill-integration-tests

## Pre-ejecución
- [ ] Tests unitarios pasando con >= 90% cobertura
- [ ] Base de datos `gastos_ia_test` creada en PostgreSQL
- [ ] Migraciones aplicadas a `gastos_ia_test`
- [ ] `tests/integration/conftest.py` configurado con pool real de prueba
- [ ] Directorio `ejemplos/` contiene imágenes de tickets
- [ ] Ollama disponible o mock configurado en conftest
- [ ] Variables `GASTOSIA_DATABASE_*` apuntan a instancia de prueba
- [ ] `.env.test` no contiene valores reales de producción
- [ ] Fixture `clean_db` trunca tablas correctamente entre tests

## Ejecución
- [ ] Tests de detección: archivo nuevo detectado, estabilidad verificada
- [ ] Tests de hash: SHA-256 calculado, duplicado exacto bloqueado
- [ ] Tests de duplicado probable: advertencia generada, no bloqueo
- [ ] Tests de cola FIFO: orden respetado, solo uno en ANALIZANDO
- [ ] Tests de atomicidad: claim_next_job con lock, sin race conditions
- [ ] Tests de extracción: JSON válido, campos normalizados, confianza evaluada
- [ ] Tests de estados: todas las transiciones válidas probadas
- [ ] Tests de estados: transiciones inválidas rechazadas
- [ ] Tests de Ollama edge cases: timeout, respuesta malformada, campos faltantes
- [ ] Tests de imagen corrupta: ERROR_PROCESAMIENTO, archivo a errores/
- [ ] Tests de imagen no-ticket: manejo graceful
- [ ] Tests de SMB lock simulado: PermissionError, EACCES, EBUSY → reintento
- [ ] Tests de concurrencia: múltiples workers, solo uno reclama trabajo
- [ ] Tests de recuperación: ANALIZANDO → EN_COLA tras reinicio
- [ ] Tests de DB fail: pérdida de conexión, reintento, no crash
- [ ] Tests de Google Sheets: inserción, pestaña mensual, _Control
- [ ] Tests de offline: PENDIENTE_DE_ENVIO, reintento al reconectar
- [ ] Tests de actualización: mismo mes, cambio de mes, conciliación
- [ ] Tests de imagen grande (>15 MB) y vacía (0 bytes)
- [ ] Al menos 20 imágenes de `ejemplos/` procesadas

## Post-ejecución
- [ ] 0 tests de integración fallidos
- [ ] Base de datos `gastos_ia_test` limpia (sin datos residuales)
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra schema
- [ ] Métricas documentadas: tests pasados, imágenes procesadas, edge cases
- [ ] Tiempo total de ejecución registrado
- [ ] Ningún secreto expuesto en outputs, logs o evidencia
- [ ] Ningún dato escrito accidentalmente en base de datos de producción
