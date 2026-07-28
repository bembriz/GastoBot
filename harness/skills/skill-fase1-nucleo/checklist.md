# Checklist — skill-fase1-nucleo

## Pre-ejecucion
- [ ] Fase 0 completada y con GATE aprobado
- [ ] Rama `arnes` activa
- [ ] PostgreSQL accesible (base `gastos_ia`, usuario `gastos_app`)
- [ ] Ollama corriendo con modelo seleccionado en Fase 0
- [ ] `harness/evidence/fase1/` existe
- [ ] AGENTS.md muestra `fase1.status == "pending"`

## Ejecucion — skill-database
- [ ] `skill-database` cargado y ejecutado
- [ ] SKILL.md instrucciones seguidas paso a paso
- [ ] checklist.md completamente marcado
- [ ] `schema-postgresql.json` generado
- [ ] `schema-postgresql.md` generado
- [ ] 9 tablas minimas creadas (PRD §18)
- [ ] Migraciones reversibles verificadas

## Ejecucion — skill-authentication
- [ ] `skill-authentication` cargado y ejecutado
- [ ] Argon2id configurado como algoritmo de hash
- [ ] Cookies HttpOnly, Secure, SameSite configuradas
- [ ] Rate limiting: 5 intentos = 15 min bloqueo
- [ ] Cambio obligatorio de contrasena en primer login
- [ ] RBAC: Ruben admin, Esme estandar
- [ ] `sistema-autenticacion.json` generado
- [ ] `sistema-autenticacion.md` generado

## Ejecucion — skill-folder-monitor
- [ ] `skill-folder-monitor` cargado y ejecutado
- [ ] Monitoreo cada 5 segundos implementado
- [ ] Validacion de estabilidad: 3 verificaciones
- [ ] Extensiones validas: .jpg, .jpeg, .png, .webp
- [ ] SHA-256 calculado para cada archivo
- [ ] EXIF: orientacion corregida
- [ ] Copia optimizada para inferencia
- [ ] Bloqueos SMB temporales capturados (no tratados como error)
- [ ] `monitor-carpetas.json` generado
- [ ] `monitor-carpetas.md` generado

## Ejecucion — skill-fifo-queue
- [ ] `skill-fifo-queue` cargado y ejecutado
- [ ] Cola FIFO con orden por enqueued_at, record_id
- [ ] Maximo 1 trabajo en ANALIZANDO
- [ ] Reclamo atomico con SELECT FOR UPDATE SKIP LOCKED
- [ ] Recuperacion de ANALIZANDO tras reinicio
- [ ] Prevencion de multiples workers
- [ ] `cola-fifo.json` generado
- [ ] `cola-fifo.md` generado

## Ejecucion — skill-image-extraction
- [ ] `skill-image-extraction` cargado y ejecutado
- [ ] Prompt estructurado segun PRD §7.2
- [ ] JSON validado (campos requeridos, tipos)
- [ ] Normalizacion: fechas ISO, montos float, tipos validos
- [ ] Confianza calculada por campo
- [ ] Manejo de JSON malformado
- [ ] Merge con EXIF (si disponible)
- [ ] `extraccion-imagenes.json` generado
- [ ] `extraccion-imagenes.md` generado

## Post-ejecucion
- [ ] 10 archivos de evidencia (5 skills x 2 formatos) presentes
- [ ] `resumen-fase1.json` generado
- [ ] `resumen-fase1.md` generado
- [ ] `skill-quality-gate` ejecutado y aprobado
- [ ] Lint, tipos, tests pasan
- [ ] Cobertura >= 90% en tests unitarios
- [ ] `fase1.status == "completed"` en AGENTS.md
- [ ] `harness/PROGRESS.md` actualizado
- [ ] GATE manual solicitado para Fase 2
