# Skill: skill-fase1-nucleo

## Identity
Eres un orquestador de Fase 1. No implementas componentes directamente; coordinas la ejecucion secuencial de los 5 skills de dominio (database, authentication, folder-monitor, fifo-queue, image-extraction), verificas sus evidencias y consolidas el reporte de fase.

## Context
La Fase 1 construye el nucleo funcional de Gastos IA: base de datos, autenticacion, deteccion de archivos, cola de procesamiento y extraccion multimodal. Es la fase mas grande del proyecto (20 horas estimadas) y su exito determina si las Fases 2-5 son viables.

Los skills se ejecutan en orden estricto porque cada uno depende del anterior:
- `skill-database` crea las tablas que todos los demas usan
- `skill-authentication` requiere tablas `users`
- `skill-folder-monitor` requiere `image_files` y `processing_queue` para registrar detecciones
- `skill-fifo-queue` requiere `processing_queue` y depende de que el monitor ya funcione
- `skill-image-extraction` requiere `extraction_runs` y que la cola FIFO este operativa

## Preconditions
- Fase 0 completada (`phases.fase0.status == "completed"`)
- GATE manual de Fase 0 aprobado por el usuario
- Rama `arnes` activa
- PostgreSQL accesible con base `gastos_ia` y usuario `gastos_app` creados
- Ollama corriendo con modelo recomendado (de Fase 0)
- `uv` funcional y dependencias base instaladas
- Directorio `harness/evidence/fase1/` existente
- Modelo decidido (2B o 4B) documentado

## Execution

### Step 0: Inicio de fase
1. Leer AGENTS.md, verificar `phases.fase0.status == "completed"`
2. Cambiar `phases.fase1.status` a `"in_progress"`
3. Actualizar `harness/PROGRESS.md` con timestamp de inicio y ETA (20 horas)
4. Crear `harness/evidence/fase1/` si no existe

### Step 1: Ejecutar skill-database
1. Cargar `harness/skills/skill-database/SKILL.md`
2. Invocar `skill-database`
3. Verificar que la skill genera estos artefactos:
   - `harness/evidence/fase1/schema-postgresql.json`
   - `harness/evidence/fase1/schema-postgresql.md`
4. Verificar que `skill-database/checklist.md` esta completamente marcado
5. Si la skill falla, reportar al usuario y DETENER la fase (no continuar)
6. Actualizar `harness/PROGRESS.md`

### Step 2: Ejecutar skill-authentication
1. Cargar `harness/skills/skill-authentication/SKILL.md`
2. Invocar `skill-authentication`
3. Verificar que genera:
   - `harness/evidence/fase1/sistema-autenticacion.json`
   - `harness/evidence/fase1/sistema-autenticacion.md`
4. Verificar checklist completado
5. Validar que los hashes son Argon2id (no MD5, SHA, bcrypt)
6. Actualizar `harness/PROGRESS.md`

### Step 3: Ejecutar skill-folder-monitor
1. Cargar `harness/skills/skill-folder-monitor/SKILL.md`
2. Invocar `skill-folder-monitor`
3. Verificar que genera:
   - `harness/evidence/fase1/monitor-carpetas.json`
   - `harness/evidence/fase1/monitor-carpetas.md`
4. Verificar checklist completado
5. Validar que el manejo de bloqueos SMB funciona (simular con archivo bloqueado)
6. Actualizar `harness/PROGRESS.md`

### Step 4: Ejecutar skill-fifo-queue
1. Cargar `harness/skills/skill-fifo-queue/SKILL.md`
2. Invocar `skill-fifo-queue`
3. Verificar que genera:
   - `harness/evidence/fase1/cola-fifo.json`
   - `harness/evidence/fase1/cola-fifo.md`
4. Verificar checklist completado
5. Validar que solo 1 trabajo puede estar en ANALIZANDO
6. Validar recuperacion de trabajos tras reinicio simulado
7. Actualizar `harness/PROGRESS.md`

### Step 5: Ejecutar skill-image-extraction
1. Cargar `harness/skills/skill-image-extraction/SKILL.md`
2. Invocar `skill-image-extraction`
3. Verificar que genera:
   - `harness/evidence/fase1/extraccion-imagenes.json`
   - `harness/evidence/fase1/extraccion-imagenes.md`
4. Verificar checklist completado
5. Validar que el prompt estructurado produce JSON valido >= 99% del tiempo
6. Validar normalizacion de campos (fechas ISO, montos float, tipos validos)
7. Actualizar `harness/PROGRESS.md`

### Step 6: Cierre de fase
1. Verificar que existen los 10 archivos de evidencia (5 skills x 2 formatos)
2. Ejecutar `skill-quality-gate` sobre TODO el codigo generado en Fase 1
3. Generar reporte consolidado de fase (ver seccion Artifacts)
4. Cambiar `phases.fase1.status` a `"completed"` en AGENTS.md
5. Actualizar `harness/PROGRESS.md` con resumen final
6. Presentar al usuario:
   - Resumen de cada skill (pass/fail + metricas clave)
   - Resultado de la puerta de calidad
   - Tiempo total vs estimado
   - Riesgos identificados
   - Solicitar GATE manual para Fase 2

## Artifacts
Ademas de los 10 archivos generados por los sub-skills, este skill genera:
- `harness/evidence/fase1/resumen-fase1.json` — Reporte consolidado
- `harness/evidence/fase1/resumen-fase1.md` — Reporte consolidado legible

## Quality Criteria
- Los 5 sub-skills se ejecutaron en orden y completaron sus checklists
- La puerta de calidad paso para todo el codigo de Fase 1
- El schema de PostgreSQL contiene las 9 tablas minimas del PRD §18
- La autenticacion usa Argon2id y cookies HttpOnly/Secure/SameSite
- El monitor detecta archivos, valida estabilidad, y maneja bloqueos SMB
- La cola FIFO garantiza exclusion mutua (max 1 en ANALIZANDO)
- La extraccion produce JSON valido en >= 99% de los casos
- Las migraciones de BD son reversibles
- Los logs JSONL se generan sin secretos
- Ningun secreto hardcodeado en ningun archivo

## Edge Cases
- **Un sub-skill falla:** detener la fase, reportar el error, no continuar hasta que se resuelva
- **La puerta de calidad falla al final:** iterar sobre los errores, arreglar, re-ejecutar
- **Dependencia circular entre skills:** no deberia ocurrir si se sigue el orden; si ocurre, reportar
- **Cambio de modelo entre Fase 0 y Fase 1:** actualizar configuracion en `skill-image-extraction`
- **Timeout en benchmark residual:** ignorar si ya se completo en Fase 0; no re-ejecutar

## References
- PRD §34 (Fases — Fase 1 completa)
- PRD §18 (PostgreSQL)
- PRD §10.1 (Autenticacion)
- PRD §8 (Carpetas y monitoreo)
- PRD §9.2 (Cola de procesamiento)
- PRD §7 (Modelo multimodal)
- Related skills: `skill-database`, `skill-authentication`, `skill-folder-monitor`, `skill-fifo-queue`, `skill-image-extraction`, `skill-quality-gate`
