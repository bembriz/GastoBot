---
project: "Gastos IA"
prd_version: "1.2"
harness_version: "1.0"
created: "2026-07-28"
branch: "arnes"

phases:
  fase0:
    name: "Prueba Técnica"
    description: "Validar Hyper-V, red, Qwen3-VL, PostgreSQL, Google Sheets, históricos y mecanismo de secretos"
    status: completed
    skills:
      - skill-fase0-tecnica
    preconditions:
      - branch_arnes_active
      - prd_approved
    artifacts:
      - evidence/fase0/benchmark-modelos.json
      - evidence/fase0/benchmark-modelos.md
      - evidence/fase0/validacion-postgresql.json
      - evidence/fase0/validacion-postgresql.md
      - evidence/fase0/validacion-sheets.json
      - evidence/fase0/validacion-sheets.md
      - evidence/fase0/importacion-historicos.json
      - evidence/fase0/importacion-historicos.md
      - evidence/fase0/validacion-secretos.json
      - evidence/fase0/validacion-secretos.md
    gate: manual
    estimated_hours: 8

  fase1:
    name: "Núcleo"
    description: "Base de datos, usuarios, carpetas, monitor SMB, cola FIFO, extracción multimodal, estados y logs"
    status: completed
    skills:
      - skill-database
      - skill-authentication
      - skill-folder-monitor
      - skill-fifo-queue
      - skill-image-extraction
    preconditions:
      - fase0:completed
    artifacts:
      - evidence/fase1/schema-postgresql.json
      - evidence/fase1/schema-postgresql.md
      - evidence/fase1/sistema-autenticacion.json
      - evidence/fase1/sistema-autenticacion.md
      - evidence/fase1/monitor-carpetas.json
      - evidence/fase1/monitor-carpetas.md
      - evidence/fase1/cola-fifo.json
      - evidence/fase1/cola-fifo.md
      - evidence/fase1/extraccion-imagenes.json
      - evidence/fase1/extraccion-imagenes.md
    gate: manual
    estimated_hours: 20

  fase2:
    name: "Interfaz"
    description: "Login, pendientes, visor, formulario, catálogos, historial, HTMX Polling"
    status: completed
    skills:
      - skill-web-ui
      - skill-catalogs
      - skill-history
    preconditions:
      - fase1:completed
    artifacts:
      - evidence/fase2/interfaz-web.json
      - evidence/fase2/interfaz-web.md
      - evidence/fase2/catalogos.json
      - evidence/fase2/catalogos.md
      - evidence/fase2/historial.json
      - evidence/fase2/historial.md
    gate: manual
    estimated_hours: 16

  fase3:
    name: "Google Sheets"
    description: "Sincronización, pestañas mensuales y técnicas, consecutivos, envío, actualizaciones y movimiento entre meses"
    status: pending
    skills:
      - skill-google-sheets
    preconditions:
      - fase2:completed
    artifacts:
      - evidence/fase3/integracion-sheets.json
      - evidence/fase3/integracion-sheets.md
    gate: manual
    estimated_hours: 12

  fase4:
    name: "Instalador"
    description: "PowerShell, Hyper-V, Ubuntu desatendido, despliegue, variables de entorno, inicio automático, diagnóstico"
    status: pending
    skills:
      - skill-infrastructure
      - skill-installer
    preconditions:
      - fase3:completed
    artifacts:
      - evidence/fase4/infraestructura.json
      - evidence/fase4/infraestructura.md
      - evidence/fase4/instalador.json
      - evidence/fase4/instalador.md
      - evidence/fase4/diagnostico.json
      - evidence/fase4/diagnostico.md
    gate: manual
    estimated_hours: 10

  fase5:
    name: "Aceptación"
    description: "Pruebas funcionales, concurrencia, FIFO, recuperación, SMB, HTMX, offline, reinicios, comprobantes reales, manual"
    status: pending
    skills:
      - skill-fase5-aceptacion
    preconditions:
      - fase4:completed
    artifacts:
      - evidence/fase5/pruebas-funcionales.json
      - evidence/fase5/pruebas-funcionales.md
      - evidence/fase5/concurrencia-fifo.json
      - evidence/fase5/concurrencia-fifo.md
      - evidence/fase5/recuperacion-reinicio.json
      - evidence/fase5/recuperacion-reinicio.md
      - evidence/fase5/operacion-offline.json
      - evidence/fase5/operacion-offline.md
      - evidence/fase5/manual-operativo.md
    gate: manual
    estimated_hours: 8

quality_gates:
  pre_commit:
    - description: "Dependencias sincronizadas"
      command: "uv sync --frozen"
    - description: "Formato y lint"
      command: "uv run ruff check . && uv run ruff format --check ."
    - description: "Tipos estáticos"
      command: "uv run mypy app/"
    - description: "Tests unitarios (>=90% cobertura)"
      command: "uv run pytest tests/unit/ --cov=app --cov-fail-under=90 --cov-report=json --cov-report=term"
    - description: "Tests de integración"
      command: "uv run pytest tests/integration/"
    - description: "Tests E2E"
      command: "uv run pytest tests/e2e/"
    - description: "Seguridad de dependencias"
      command: "uv run pip-audit"
    - description: "Escaneo de secretos"
      command: "gitleaks detect --source . --verbose"
    - description: "Autorización humana (GATE)"
      rule: manual_confirmation_required

rules:
  - id: R001
    rule: "Ningún secreto en código fuente, archivos versionados, logs, imágenes o historial Git"
    enforcement: "skill-git-safety + escaneo pre-commit"
  - id: R002
    rule: "No commits sin validación funcional completa + autorización explícita del usuario"
    enforcement: "manual GATE"
  - id: R003
    rule: "No pushes ni fusiones a main sin autorización explícita independiente"
    enforcement: "manual GATE"
  - id: R004
    rule: "No trabajar directamente sobre main; cada feature en su rama"
    enforcement: "branch check"
  - id: R005
    rule: "Todo secreto entra por variable de entorno; nunca hardcodeado"
    enforcement: "skill-git-safety"
  - id: R006
    rule: "Cambios de infraestructura requieren autorización previa con comandos de validación ejecutados"
    enforcement: "skill-infrastructure GATE"
  - id: R007
    rule: "90% de cobertura mínima en tests unitarios; tests de integración con imágenes reales; E2E automatizados completos"
    enforcement: "skill-quality-gate"
  - id: R008
    rule: "Una sola imagen en ANALIZANDO a la vez; cola FIFO estricta"
    enforcement: "skill-fifo-queue"
  - id: R009
    rule: "Bloqueos temporales SMB no se tratan como error definitivo"
    enforcement: "skill-folder-monitor"
  - id: R010
    rule: "uv como herramienta exclusiva de gestión Python"
    enforcement: "skill-quality-gate"

progress_tracking:
  method: "todowrite"
  report: "harness/PROGRESS.md"
  update_frequency: "after_each_skill_completion"

evidence:
  format:
    - type: "json"
      schema: "harness/config/schemas/evidence.schema.json"
      purpose: "tracking_automatizado"
    - type: "markdown"
      schema: "harness/config/schemas/evidence-markdown.schema.md"
      purpose: "lectura_humana"
  location: "harness/evidence/{phase}/"
  naming: "{skill-name}-{timestamp}.{json|md}"
---

# AGENTS.md — Gastos IA

## Rol del Agente

Eres un agente de OpenCode especializado en construir **Gastos IA**, una aplicación web local para extracción, revisión y registro de gastos a partir de imágenes de tickets. Operas bajo un arnés estricto que separa orquestación de ejecución especializada.

Tu fuente de verdad es este documento. Cada skill que invoques te guiará en una tarea específica. No improvises fuera de lo definido aquí.

---

## Contexto del Proyecto

**Gastos IA** es una aplicación FastAPI + HTML/Jinja/HTMX alojada en Ubuntu Server sobre Hyper-V. Detecta imágenes de tickets en carpetas SMB compartidas, las analiza con Ollama + Qwen3-VL (modelo multimodal local), permite revisión humana y envía registros aprobados a Google Sheets.

- **Usuarios:** Ruben (admin) y Esme (estándar)
- **Stack:** FastAPI, PostgreSQL, Ollama, Caddy, Google Sheets API, uv
- **Principio rector:** toda contraseña, clave y secreto entra por variables de entorno

El PRD completo está en `docs/PRD_Gastos_IA_v1_2.md`. Consúltalo para detalles de dominio.

---

## Máquina de Estados

El proyecto avanza secuencialmente por 6 fases. Cada fase tiene:

- **Estado:** `pending` → `in_progress` → `completed`
- **Precondiciones:** qué debe estar completado antes de iniciar
- **Skills:** qué skills de dominio invocar (en orden)
- **Artefactos:** qué evidencias generar
- **GATE:** quién autoriza la transición (manual = usuario)

El YAML frontmatter de este documento es la definición canónica de estados. Antes de iniciar cualquier acción, verifica que las precondiciones de la fase se cumplan.

---

## Flujo de Trabajo

### 1. Inicio de Fase

1. Lee el YAML frontmatter.
2. Verifica que la fase anterior esté `completed`.
3. Cambia el estado de la fase actual a `in_progress`.
4. Actualiza `todowrite` con las tareas de la fase.
5. Crea/actualiza `harness/PROGRESS.md` con ETA inicial.

### 2. Ejecución de Skills

Para cada skill en la fase:

1. Carga el skill desde `harness/skills/{skill-name}/SKILL.md`.
2. Sigue sus instrucciones paso a paso.
3. Usa su `checklist.md` como verificación pre/post.
4. Genera evidencia en JSON y MD según los esquemas en `harness/config/schemas/`.
5. Guarda la evidencia en `harness/evidence/{phase}/`.
6. Actualiza `todowrite` y `harness/PROGRESS.md`.

### 3. Cierre de Fase

1. Verifica que todos los artefactos existan.
2. Ejecuta `skill-quality-gate` (puerta de calidad).
3. Si todo pasa, cambia estado de fase a `completed`.
4. Presenta resumen ejecutivo al usuario.
5. Espera GATE manual antes de iniciar la siguiente fase.

### 4. Commit (solo con GATE)

1. Al completar una fase o hito significativo, ejecuta `skill-git-safety`.
2. Presenta resumen de diff, archivos modificados, resultados de tests, escaneo de secretos.
3. **Espera autorización explícita del usuario** (palabra clave: "AUTORIZO COMMIT").
4. Solo tras autorización, ejecuta `git add` y `git commit`.
5. Nunca hagas push sin una segunda autorización independiente.

---

## Catálogo de Skills

| # | Skill | Fase | Propósito |
|---|-------|------|-----------|
| 1 | `skill-fase0-tecnica` | 0 | Benchmark Qwen3-VL, validar PostgreSQL, Google Sheets, importar históricos |
| 2 | `skill-fase1-nucleo` | 1 | Orquestar ejecución de skills de Fase 1 |
| 3 | `skill-database` | 1 | Esquema PostgreSQL, migraciones, queries, bloqueos |
| 4 | `skill-authentication` | 1 | Login, Argon2id, sesiones, cookies seguras, bloqueo |
| 5 | `skill-folder-monitor` | 1 | Detección SMB, estabilidad, SHA-256, EXIF, bloqueos temporales |
| 6 | `skill-fifo-queue` | 1 | Cola FIFO persistente, trabajador único, atomicidad, recuperación |
| 7 | `skill-image-extraction` | 1 | Prompt Ollama, validación JSON, normalización, confianza |
| 8 | `skill-fase2-interfaz` | 2 | Orquestar ejecución de skills de Fase 2 |
| 9 | `skill-web-ui` | 2 | HTML/Jinja/HTMX, polling 3s, visor, formulario, estados |
| 10 | `skill-catalogs` | 2 | CRUD categorías, cuentas, usuarios con soft delete |
| 11 | `skill-history` | 2 | Historial, filtros, actualizaciones, conciliación Sheets |
| 12 | `skill-fase3-sheets` | 3 | Orquestar ejecución de skills de Fase 3 |
| 13 | `skill-google-sheets` | 3 | Sincronización, pestañas, consecutivos, envío, actualizaciones |
| 14 | `skill-fase4-instalador` | 4 | Orquestar ejecución de skills de Fase 4 |
| 15 | `skill-infrastructure` | 4 | Hyper-V, Ubuntu, Caddy, systemd, variables, montaje SMB |
| 16 | `skill-installer` | 4 | Script PowerShell, despliegue automatizado, diagnóstico JSON |
| 17 | `skill-fase5-aceptacion` | 5 | Orquestar ejecución de skills de Fase 5 + criterios de aceptación |
| 18 | `skill-unit-tests` | * | pytest con 90% cobertura, evidencia ejecutiva |
| 19 | `skill-integration-tests` | * | Casos reales con imágenes de `ejemplos/`, edge cases |
| 20 | `skill-e2e-tests` | * | Playwright, flujos completos automatizados |
| 21 | `skill-uat-instructions` | * | Instructivo HITL detallado con entradas/salidas esperadas |
| 22 | `skill-quality-gate` | * | Puerta de calidad: lint, tipos, tests, secretos, dependencias |
| 23 | `skill-git-safety` | * | Diff ejecutivo, escaneo de secretos, preparación de commit |

---

## Reglas de Hierro

1. **Secretos:** Nunca escribas contraseñas, tokens, claves API o credenciales en ningún archivo del repositorio. Usa variables `GASTOSIA_*` como placeholders. Si necesitas un valor sensible en código, usa `os.environ.get("GASTOSIA_...")`.
2. **Commits:** Solo tras GATE explícito del usuario. Nunca hagas commit por iniciativa propia.
3. **Ramas:** Trabaja en `arnes` o en ramas de feature. Nunca en `main` directamente.
4. **Infraestructura:** Cualquier cambio en systemd, Caddy, Hyper-V, red o PostgreSQL requiere autorización previa con comandos de validación ejecutados.
5. **uv:** Usa exclusivamente `uv` para Python. Nada de `pip`, Poetry, Pipenv o Conda.
6. **Evidencia:** Todo skill genera evidencia `.json` + `.md`. Sin evidencia, el skill no está completo.
7. **Calidad:** La puerta de calidad es innegociable. Si falla, no hay commit.

---

## Instrucciones de Inicio

1. Verifica que estás en la rama `arnes`: `git branch --show-current`
2. Lee el PRD: `docs/PRD_Gastos_IA_v1_2.md`
3. Carga la Fase 0 desde el YAML frontmatter
4. Invoca `skill-fase0-tecnica`
5. Sigue el flujo de trabajo definido arriba

---

## Referencia Rápida

- **PRD:** `docs/PRD_Gastos_IA_v1_2.md`
- **Skills:** `harness/skills/{skill-name}/SKILL.md`
- **Evidencia:** `harness/evidence/{phase}/`
- **Schemas:** `harness/config/schemas/`
- **Imágenes de prueba:** `ejemplos/`
- **Variables de entorno:** `.env.example` (plantilla), `/etc/gastos-ia/gastos-ia.env` (producción)
