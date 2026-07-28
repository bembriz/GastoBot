# Arnés Gastos IA — README

## Propósito

Este directorio contiene el **arnés de desarrollo** de Gastos IA. Separa la orquestación del proyecto (definida en `AGENTS.md`) de las habilidades especializadas (skills) que ejecutan cada tarea concreta.

## Estructura

```
harness/
├── skills/          # 23 skills especializados
├── evidence/        # Reportes ejecutivos generados (JSON + MD)
├── config/
│   └── schemas/     # Schemas JSON y plantillas para evidencias
├── PROGRESS.md      # Tracking de progreso con ETAs
└── README.md        # Este archivo
```

## Skills

Cada skill es una carpeta auto-contenida con:

| Archivo | Propósito |
|---|---|
| `SKILL.md` | Instrucciones paso a paso para el agente |
| `checklist.md` | Lista de verificación pre/post ejecución |
| `evidence-template.md` | Plantilla del reporte ejecutivo específico del skill |
| `examples/` | Scripts, comandos y configuraciones de ejemplo |
| `templates/` | Plantillas de salida esperada (esquemas SQL, configs, etc.) |

### Skills de Fase

| Skill | Fase | Descripción |
|---|---|---|
| `skill-fase0-tecnica` | 0 | Benchmark Qwen3-VL, validar PostgreSQL/Sheets, importar históricos |
| `skill-fase1-nucleo` | 1 | Orquestar skills de Fase 1 |
| `skill-database` | 1 | Esquema PostgreSQL, migraciones, queries, bloqueos |
| `skill-authentication` | 1 | Login, Argon2id, sesiones, cookies seguras |
| `skill-folder-monitor` | 1 | Detección SMB, SHA-256, EXIF, bloqueos temporales |
| `skill-fifo-queue` | 1 | Cola FIFO persistente, trabajador único, atomicidad |
| `skill-image-extraction` | 1 | Prompt Ollama, validación JSON, normalización |
| `skill-fase2-interfaz` | 2 | Orquestar skills de Fase 2 |
| `skill-web-ui` | 2 | HTML/Jinja/HTMX, polling 3s, visor, formulario |
| `skill-catalogs` | 2 | CRUD categorías, cuentas, usuarios con soft delete |
| `skill-history` | 2 | Historial, filtros, actualizaciones, conciliación |
| `skill-fase3-sheets` | 3 | Orquestar skills de Fase 3 |
| `skill-google-sheets` | 3 | Sincronización, pestañas, consecutivos, envío |
| `skill-fase4-instalador` | 4 | Orquestar skills de Fase 4 |
| `skill-infrastructure` | 4 | Hyper-V, Ubuntu, Caddy, systemd, montaje SMB |
| `skill-installer` | 4 | Script PowerShell, despliegue, diagnóstico |
| `skill-fase5-aceptacion` | 5 | Orquestar skills de Fase 5 + criterios de aceptación |

### Skills Transversales

| Skill | Descripción |
|---|---|
| `skill-unit-tests` | pytest con 90% cobertura |
| `skill-integration-tests` | Casos reales con imágenes de `ejemplos/` |
| `skill-e2e-tests` | Playwright, flujos completos automatizados |
| `skill-uat-instructions` | Instructivo HITL detallado |
| `skill-quality-gate` | Puerta de calidad: lint, tipos, tests, secretos |
| `skill-git-safety` | Diff ejecutivo, escaneo de secretos, preparación de commit |

## Evidencia

Cada skill genera dos reportes por ejecución:

- **JSON** (`evidence/{fase}/{skill-name}-{timestamp}.json`): tracking automatizado, evaluación de precondiciones
- **Markdown** (`evidence/{fase}/{skill-name}-{timestamp}.md`): lectura humana, resumen ejecutivo

Ambos formatos siguen schemas definidos en `config/schemas/`.

## Flujo de Trabajo

1. El agente lee `AGENTS.md` (raíz del repo)
2. Identifica la fase activa y sus skills
3. Por cada skill: carga SKILL.md, ejecuta checklist.md, genera evidencia
4. Al completar la fase: ejecuta skill-quality-gate, espera GATE manual
5. Al recibir autorización: ejecuta skill-git-safety, presenta diff, espera commit

## Reglas

- No commits sin GATE explícito del usuario
- No secretos en código fuente
- uv como herramienta exclusiva Python
- Infraestructura: autorización previa con validación ejecutada

---

*Arnés v1.0 — Gastos IA*
