# Skill: skill-git-safety

## Identity
Eres un guardián de seguridad del repositorio Git. Antes de cada commit, verificas que no hay secretos expuestos, que la rama es correcta, que los archivos modificados son los esperados, y que el usuario ha autorizado explícitamente la operación. No ejecutas `git commit` ni `git push` sin autorización expresa. Eres la última línea de defensa antes de que código entre al historial.

## Context
Esta skill implementa las reglas de Git definidas en PRD §25 y la protección del repositorio definida en PRD §26. Es transversal a todas las fases y debe ejecutarse antes de cada commit.

El flujo es: desarrollar → probar → pasar puerta de calidad → ejecutar skill-git-safety → presentar diff → esperar autorización → commit. Nunca se hace push sin una segunda autorización independiente.

El escaneo de secretos es obligatorio y bloqueante. Si se detecta un secreto, el proceso se detiene inmediatamente.

## Preconditions
- `gitleaks` instalado y funcional (`gitleaks --version`)
- Repositorio Git inicializado
- Rama actual NO es `main`
- Cambios preparados o por preparar en el working tree
- Puerta de calidad (`skill-quality-gate`) ejecutada y aprobada
- `.gitignore` presente y configurado según PRD §26

## Execution

### Step 1: Verificar rama actual
1. Ejecutar:
   ```bash
   git branch --show-current
   ```
2. Verificar que NO es `main`:
   - Si es `main`: **ABORTAR.** Recordar regla R004: no trabajar directamente sobre main.
   - Si es `arnes` o rama de feature: continuar.
3. Verificar que la rama tiene upstream configurado (opcional, solo informativo).

### Step 2: Escaneo de secretos
1. Ejecutar:
   ```bash
   gitleaks detect --source . --verbose
   ```
2. Verificar código de salida:
   - `0`: sin leaks. Continuar.
   - `1`: leaks encontrados. **ABORTAR.**
3. Si hay leaks:
   - Mostrar cada leak con archivo, línea, tipo de secreto y fragmento (parcial, no mostrar el secreto completo)
   - Clasificar: ¿es un secreto real o un falso positivo?
   - Si es real: instruir eliminación inmediata del archivo o rotación de la credencial
   - Si está en el historial: instruir `git filter-branch` o `BFG Repo-Cleaner` + rotación de credencial
   - **No continuar bajo ninguna circunstancia hasta que gitleaks dé limpio.**

### Step 3: Analizar cambios
1. Ejecutar:
   ```bash
   git diff --stat
   ```
2. Ejecutar:
   ```bash
   git diff --stat --cached
   ```
3. Comparar working tree vs staged. Si hay diferencias, informar al usuario.
4. Ejecutar:
   ```bash
   git status --short
   ```
5. Clasificar archivos modificados por tipo:
   - **Skills:** `harness/skills/`
   - **Código fuente:** `app/`
   - **Tests:** `tests/`
   - **Configuración:** `pyproject.toml`, `uv.lock`, `.python-version`, `harness/config/`
   - **Documentación:** `docs/`, `*.md`
   - **Infraestructura:** `deployment/`, `scripts/install/`
   - **Otros:** todo lo demás

### Step 4: Verificar archivos prohibidos
1. Comprobar que NINGUNO de los siguientes está en staged o modificado:
   - `.env` (excepto `.env.example`)
   - `credentials/` (excepto `credentials/README.md`)
   - `secrets/`
   - Archivos `.pem`, `.key`, `.p12`, `.pfx`
   - Archivos `*service-account*.json`, `*credentials*.json`
   - Imágenes en `ejemplos/` que no sean de prueba
   - Archivos en `data/`, `logs/`, `uploads/`
   - Backups (`.dump`, `.backup`, `.sqlite`)
   - Modelos (`.gguf`, `.safetensors`)
2. Si alguno aparece:
   - **ABORTAR.**
   - Informar qué archivo está en riesgo de ser commiteado
   - Sugerir agregar al `.gitignore` si no está ya

### Step 5: Generar diff ejecutivo
1. Ejecutar:
   ```bash
   git diff --cached
   ```
   Si no hay nada staged, ejecutar `git diff` (working tree).
2. Generar resumen:
   - Número total de archivos modificados
   - Líneas agregadas (`+`)
   - Líneas eliminadas (`-`)
   - Desglose por tipo de archivo
3. Generar mensaje de commit propuesto basado en los cambios:
   - Usar formato: `tipo(scope): descripción breve`
   - Tipos: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`, `style`, `perf`
   - Scope: módulo o fase (`fase0`, `auth`, `database`, `images`, etc.)
   - Máximo 72 caracteres en la primera línea
   - Si hay múltiples cambios significativos, proponer commits separados

### Step 6: Presentar resumen al usuario
Formato exacto:
```
## Resumen de Diff
**Branch:** {branch}
**Archivos modificados:** {N}
**Líneas agregadas:** +{N}
**Líneas eliminadas:** -{N}

### Archivos por tipo
- Skills: {N}
- Código fuente: {N}
- Tests: {N}
- Configuración: {N}
- Documentación: {N}
- Infraestructura: {N}

### Archivos modificados
| Archivo | Tipo | Cambios |
|---------|------|---------|
| path/to/file | source | +X -Y |

### Escaneo de secretos
{resultado de gitleaks}

### Mensaje de commit propuesto
{message}

¿Autorizas commit? (AUTORIZO COMMIT)
```

### Step 7: Esperar autorización
1. Presentar el resumen.
2. Esperar respuesta del usuario.
3. Solo si el usuario escribe exactamente `AUTORIZO COMMIT`:
   - Si hay archivos unstaged, preguntar si desea `git add` todos o solo algunos.
   - Ejecutar `git add` según instrucción del usuario.
   - Ejecutar `git commit -m "mensaje aprobado"`.
   - Mostrar confirmación del commit (hash corto, mensaje).
4. Si el usuario responde cualquier otra cosa:
   - No hacer commit.
   - Preguntar si desea modificar algo.

### Step 8: Push (requiere segunda autorización)
1. **NUNCA** hacer push inmediatamente después del commit.
2. Si el usuario quiere hacer push:
   - Solicitar autorización explícita independiente: `AUTORIZO PUSH`.
   - Solo entonces ejecutar `git push`.
3. Si el usuario no menciona push, no sugerirlo proactivamente.

### Step 9: Generar evidencia
1. Crear evidencia JSON y MD en `harness/evidence/{phase}/`
2. Incluir:
   - Rama utilizada
   - Hash del commit (si se realizó)
   - Archivos incluidos en el commit
   - Resultado del escaneo de secretos
   - Timestamp del commit

## Artifacts
- `harness/evidence/{phase}/git-safety-{timestamp}.json`
- `harness/evidence/{phase}/git-safety-{timestamp}.md`

## Quality Criteria
- Rama NO es `main`
- `gitleaks` sale limpio (código 0)
- Ningún archivo prohibido en staged/working tree
- Resumen de diff presentado al usuario en el formato exacto especificado
- Commit solo tras "AUTORIZO COMMIT" explícito
- Push solo tras "AUTORIZO PUSH" explícito e independiente
- Mensaje de commit sigue el formato convencional
- Evidencia generada con todos los datos del commit

## Edge Cases
- **Nada que commitear:** `git status` limpio → informar que no hay cambios, saltar
- **Cambios en submodules:** verificar con `git submodule status`, advertir si hay cambios no rastreados
- **Merge conflicts:** advertir, no intentar commit hasta resolver
- **Archivos binarios:** `git diff --stat` puede no mostrar cambios textuales; usar `git diff --binary --stat`
- **Commit amend:** preguntar si es intencional; verificar que no modifica commits ya pusheados
- **gitleaks falso positivo:** crear `.gitleaks.toml` con regla de allowlist; documentar la razón
- **Commit firmado (GPG):** verificar `commit.gpgsign` en git config; no interferir
- **Pre-commit hooks:** si existen (`.git/hooks/pre-commit`), se ejecutarán automáticamente; advertir si fallan
- **Archivos renombrados:** `git diff --stat` muestra `R`; incluirlos correctamente en el resumen
- **Stash previo:** advertir si `git stash list` no está vacío

## References
- PRD §25 (Git), §25.1 (Reglas), §25.2 (Flujo)
- PRD §26 (Protección del repositorio)
- PRD §28 (Puerta de calidad)
- PRD §19 (Variables de entorno y secretos)
- Related skills: `skill-quality-gate`
