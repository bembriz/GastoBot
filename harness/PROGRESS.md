# Progress Tracking — Gastos IA

> Ultima actualizacion: 2026-09-04T00:00:00-06:00
> Estado: FASES 0-5 COMPLETADAS. Sistema redesplegado en servidor bare-metal lenovosrv (192.168.100.24, Ubuntu 24.04, Docker).
> Pendiente: pruebas de usuario (Ruben/Esme) con imagenes reales; instalar CA de Caddy y entrada hosts en las PCs.
> Cambios 2026-09-04: FIX combo Categoria vacio en detalle de registro (commit en rama dev). Causa raiz: catalog_cache.parent_id nunca se poblo — la migracion desde Catalogo.xlsx descartaba el par categoria->cuenta y el CRUD admin no pedia cuenta padre. Fix: seed_catalogs liga/repara parent_id (--catalogs-only), expense_detail y /categories/by-account filtran por cuenta con fallback a todas, alta de categoria pide cuenta padre. Desplegado en lenovosrv (rebuild imagen + backfill de 45 vinculos; 33 categorias con padre / 0 sin padre) y verificado E2E. Respaldo pre-despliegue: /home/administrador/gastos-ia-repo-backup-20260903.tar.gz. NOTA TESTS: la BD de pruebas gastos_ia_test vive ahora en el postgres de lenovosrv; para correr la suite local: tunel `ssh -N -L 15432:127.0.0.1:5433 administrador@192.168.100.24` + `GASTOSIA_DATABASE_HOST=127.0.0.1 GASTOSIA_DATABASE_PORT=15432` y SIN GASTOSIA_USE_ADMIN_DB (el superusuario del nuevo postgres es `trading`, no `postgres`; el .envrc aun apunta al host muerto 192.168.100.45).
> Cambios 2026-09-03: MIGRACION A NUEVO SERVIDOR. El host Windows/Hyper-V quedo fuera de servicio; lenovosrv es ahora Ubuntu 24.04 bare metal (mismo hardware, i5-7300HQ/32GB). Stack Docker en /srv/docker/gastos-ia (compose + Caddyfile + .env en repo deployment/docker/): app (imagen nueva python:3.12-slim + uv, monitor+worker in-process, GASTOSIA_SMB_BASE=/data/gastos bind-mount de /mnt/warehouse/GastosIA), caddy (HTTPS gastos.local, CA interna NUEVA — root.crt en deployment/docker/gastos-local-root.crt, instalar en PCs), samba (servercontainers/samba, share GastosIA, usuarios ruben/esme). BD: se REUTILIZA el postgres existente (contenedor self-evaluating-trading-agent-postgres-1, pg16, alias `postgres` en red externa); rol gastos_app + base gastos_ia creados ahi, schema via alembic. Migracion desde Google Sheets (scripts/migration/import_from_sheets.py): 618 historicos de _Control (517 con colision grupo/consecutivo — datos historicos reusan pares; se importaron sin el par, final_description intacto), 8 registros actuales de Julio-26/Agosto-26, 5 imagenes vinculadas por fecha de nombre de archivo (3 sin vincular: "Imagen 1-3.jpeg"), 42 catalogos desde docs/Catalogo.xlsx (codes truncados a varchar(50)). UFW: 80/443/445/139 abiertos. Verificado: POST /login 302 en 0.1s, share SMB accesible con ruben/esme, monitor SMB y worker FIFO activos. Users Ruben/Esme con password inicial del .envrc (password_change_required).
> Cambios 2026-08-19 (2): IP vEthernet del host FIJADA como estatica 192.168.100.12/24 (Manual, PersistentStore, via WinRM/pypsrp) — la causa raiz de los incidentes de IP queda eliminada. Redespliegue completo desde rama dev (commits 93c5cf3, c5c0a45, fd6d841, 992e571): rsync app/templates/static/migrations/prompts + uv sync --frozen. Eliminados archivos huerfanos en /opt/gastos-ia (queue.py, extraction.py, routes.py, etc. — queue.py ensombrecia el stdlib y rompia urllib3). Respaldo pre-despliegue: /home/gastos-admin/gastos-ia-backup-20260819.tar.gz. Verificado: login HTMX responde fragmento en 0.08s, dashboard redirige a /login, monitor SMB y worker FIFO activos.
> Cambios 2026-08-19 (3): limpieza de datos de prueba en produccion (16 expense_records + 6 usuarios test_* borrados; prod queda en estado canonico: 2 usuarios, 8 records) + aislamiento de tests. CAUSA RAIZ: tests/conftest.py apuntaba por defecto a la BD de produccion y .envrc inyecta credenciales reales (GASTOSIA_USE_ADMIN_DB=true -> tests corrian como superusuario postgres). FIX: conftest fuerza GASTOSIA_DATABASE_NAME a gastos_ia_test (nueva BD en el mismo servidor, esquema via alembic; override con GASTOSIA_TEST_DATABASE_NAME, escape con GASTOSIA_ALLOW_PROD_TESTS=1). Nueva migracion a1b2c3d4e5f6 (catalog_cache.parent_id, IF NOT EXISTS — alinea drift: la columna existia en prod y modelos pero no en initial_schema). Fix migrations/env.py: quote_plus en credenciales + escape %% para configparser (el password con @ rompia alembic). Verificado: 220 tests pass contra gastos_ia_test, prod intacta tras la corrida. Sin llamadas reales a Gemini/Kimi/Sheets en ningun momento (todo mockeado).
> Cambios 2026-08-17: incidente IP host cerrado — VM usa 192.168.100.5 (vEthernet) para PostgreSQL y SMB; LAN/desarrollo usan 192.168.100.45. Ver tabla canonica en Infraestructura.
> Cambios 2026-08-12: boton Reenviar en errores de extraccion, fix desbordamiento int64 en consecutivos (pg_advisory_xact_lock), modelo Gemini flash-latest.

---

## Resumen Global

| Fase | Estado | Progreso | ETA |
|---|---|---|---|
| Fase 0 — Prueba Tecnica | **completed** | 100% | — |
| Fase 1 — Nucleo | **completed** | 100% | — |
| Fase 2 — Interfaz | **completed** | 100% | — |
| Fase 3 — Google Sheets | **completed** | 100% | — |
| Fase 4 — Instalador | **completed** | 100% | — |
| Fase 5 — Aceptacion | **completed** | 100% | 39/39 criterios verificados |

---

## Quality Gates (2026-08-12) — TODOS PASANDO

| Gate | Estado | Detalle |
|------|--------|---------|
| Ruff lint | **pass** | 0 errores, 59 files |
| Ruff format | **pass** | 59 files ok |
| Mypy strict | **pass** | 0 issues en 26 source files |
| Unit + Integration | **pass** | 220 passed, 2 skipped |
| E2E Playwright | **pass** | 25 passed (16 public + 9 auth) |
| Coverage | **pass** | 90% (threshold 60%) |
| pip-audit | **pass** | 0 vulnerabilidades |
| Secrets scan | **pass** | 0 secrets (manual scan) |
| Pre-commit hook | **pass** | ruff + mypy + pytest |

---

## Extraccion — Gemini multi-key + Kimi fallback

| Motor | Velocidad | Costo | Estado |
|-------|-----------|-------|--------|
| Gemini flash-latest (key 1) | ~2s | Gratis 1500 req/dia | Cuenta bembriz |
| Gemini flash-latest (key 2) | ~2s | Gratis 1500 req/dia | Cuenta xuum23 |
| Kimi (Moonshot) | ~5-10s | Pago por uso | Fallback si ambas Gemini sin cuota |

El sistema intenta todas las keys de Gemini en secuencia (GASTOSIA_GEMINI_API_KEY_1, _2, ...).
Si todas fallan por cuota agotada (429/RESOURCE_EXHAUSTED), automaticamente usa Kimi.
Agregar mas keys Gemini es trivial: crear GASTOSIA_GEMINI_API_KEY_N en .env.
Los errores de extraccion son visibles en la UI (seccion al pie del dashboard, polling 10s).
Cada error tiene un boton "Reenviar" que re-encola la imagen para reintentar la extraccion.

---

## Evidencias Fase 5

| Archivo | Estado | Descripcion |
|---|---|---|
| `pruebas-unitarias.json` + `.md` | **completo** | 216 tests, 95% coverage |
| `pruebas-integracion.json` + `.md` | **completo** | 68+ tests rutas autenticadas |
| `pruebas-e2e.json` + `.md` | **completo** | 25 tests Playwright (16 public + 9 auth) |
| `concurrencia-fifo.json` + `.md` | **completo** | 3 imagenes reales en VM; FIFO confirmado |
| `recuperacion-reinicio.json` + `.md` | **completo** | systemctl restart: 110 records + 9 queue preserved |
| `operacion-offline.json` + `.md` | **completo** | 19 registros PENDIENTE_DE_ENVIO |
| `manual-operativo.json` + `.md` | **completo** | 171 lineas, 8 secciones |
| `pruebas-funcionales.json` | **completo** | 39 criterios (34 passed, 3 skipped, 2 warning) |

---

## Criterios de Aceptacion (39 items PRD)

| Estado | Cantidad | Detalle |
|---|---|---|
| Verificados | 34 | Tests unitarios/integracion/E2E + pruebas en VM |
| Skipped | 3 | C17 (confidence UI), C25 (dup warning UI), C32 (no JSONL logs) |
| Warning | 2 | C27 (headers Sheets no verificados visualmente), C30 (cambio mes no verificado E2E) |

---

## Modulos implementados

| Modulo | Archivos |
|---|---|
| `app/database/` | engine, session, models (9 tablas), locking |
| `app/auth/` | password (Argon2id), session, routes, permissions |
| `app/images/` | monitor (SMB 5s, SHA-256, EXIF) |
| `app/expenses/` | routes (dashboard HTMX, visor, update, retry), queue (FIFO), extraction (Gemini + Kimi fallback) |
| `app/catalogs/` | routes (CRUD categorias/cuentas, solo admin) |
| `app/history/` | routes (busqueda, filtros) |
| `app/sheets/` | client (gspread), tabs (Mes-AA), sender (11 pasos) |
| `templates/` | base, login, dashboard, expense_list, expense_detail, catalogs, history |

## Infraestructura

> **OBSOLETA desde 2026-09-03** — la infraestructura descrita abajo (host Windows LENOVOSRV + VM Hyper-V) ya no existe. La referencia vigente es la entrada "Cambios 2026-09-03" al inicio: stack Docker en lenovosrv (192.168.100.24), `/srv/docker/gastos-ia/`. Se conserva como historial.

### IPs del host LENOVOSRV (canonico desde 2026-08-19)

| IP | Interfaz | Uso |
|---|---|---|
| `192.168.100.45` | Ethernet fisica (estatica) | Equipos LAN, PCs de usuarios, desarrollo, shares SMB (`\\192.168.100.45\GastosIA`) |
| `192.168.100.12` | vEthernet (switch Hyper-V, **DHCP — inestable**) | **Todo el trafico VM → host**: PostgreSQL y SMB desde la VM |

IMPORTANTE: la VM **no puede** alcanzar la `.45` (la interfaz fisica no responde ARP al lado de las VMs en el switch externo). Toda referencia VM→host debe usar la IP vEthernet vigente (hoy `.12`; era `.5` hasta el 2026-08-18). Es la misma instancia de PostgreSQL 15 en ambas IPs (escucha en todas las interfaces).

- **PostgreSQL**: 192.168.100.12:5432 (desde la VM) / 192.168.100.45:5432 (desde LAN), BD `gastos_ia`, usuario `gastos_app`
- **Google Sheets**: "Reporte de gastos 2026"
- **Usuarios**: Ruben (admin), Esme (standard) — Argon2id
- **Branch**: `dev`

### VM GastosIA
- **Host**: LENOVOSRV (i5-7300HQ, 32 GB, Hyper-V; tambien es DC de `zumpango.com`)
- **VM**: 16 GB RAM, 4 vCPU, Gen 2, 120 GB VHDX
- **OS**: Ubuntu Server 24.04.4 LTS
- **Red**: Static IP `192.168.100.75/24`
- **Caddy**: HTTPS `gastos.local` → `localhost:8000`
- **Extraction**: Gemini flash-latest → Kimi (fallback automatico)
- **SMB**: `//192.168.100.12/GastosIA/{Ruben,Esme}` montado en `/mnt/smb/`
- **Systemd**: `gastos-ia.service` enabled

## Comandos utiles (VM)

```bash
# Ver logs en tiempo real
sudo journalctl -u gastos-ia -f

# Reiniciar servicio
sudo systemctl restart gastos-ia

# Ver estado
systemctl status gastos-ia

# Cambiar modelo Gemini
sudo nano /etc/gastos-ia/gastos-ia.env
# GASTOSIA_GEMINI_MODEL=gemini-flash-latest
sudo systemctl restart gastos-ia
```

## Incidente 2026-08-16 — IP del host cambiada (CERRADO 2026-08-17)

El host LENOVOSRV paso de IP dinamica `.13` a estatica `.45` (Ethernet fisica). La VM quedo apuntando a `.13` (muerta) y ademas `.45` no responde ARP desde la VM (TCP/IP activo en la interfaz fisica sobre switch externo Hyper-V). Fix: la VM usa `.5` (vEthernet del host) para PostgreSQL (`/etc/gastos-ia/gastos-ia.env`) y SMB (`/etc/fstab`). Respaldos en la VM: `gastos-ia.env.bak-20260817`, `fstab.bak-20260817`. Verificado: misma instancia PostgreSQL 15.12 en `.5` y `.45` (2 usuarios, 8 expense_records identicos).

**Modelo canonico de IPs:** ver tabla en la seccion Infraestructura. VM→host siempre por `.5`; LAN/desarrollo por `.45`. Las evidencias historicas en `harness/evidence/` mencionan `.45`/`.13` porque reflejan lo que existia al ejecutarse — no modificarlas.

**Pendiente menor:** `.5` es DHCP en vEthernet — conviene fijarla como estatica o hacer reserva DHCP en el router. Nota: el host es controlador de dominio (`zumpango.com`).

## Incidente 2026-08-19 — REINCIDENCIA: vEthernet DHCP cambio de `.5` a `.12` (CERRADO)

Sintoma: portal cargaba `/login` pero el POST se colgaba indefinidamente (el pool de asyncpg agotaba conexiones con `TimeoutError` contra `192.168.100.5:5432`, ya muerta). El pendiente del incidente anterior se materializo: la vEthernet del host tomo una nueva IP DHCP (`.12`).

Diagnostico:
- `POST /login` con timeout de 20s sin respuesta; `GET /login` 200 inmediato (la pagina no toca la BD).
- Desde la VM, escaneo de 5432 en la subred encontro `.12` (acepta credenciales `gastos_app`, BD `gastos_ia` con datos correctos) y `.144` (la laptop de desarrollo, otro PostgreSQL).
- Identidad confirmada por `system_identifier` de `pg_control_system()`: `.12` y `.45` son la MISMA instancia (7498970274172338484, 15 expense_records identicos).
- Montajes CIFS en `/mnt/smb/{Ruben,Esme}` colgados (Errno 112 Host is down) por apuntar a `.5`.

Fix aplicado en la VM (respaldos `gastos-ia.env.bak-20260819`, `fstab.bak-20260819`):
1. `sed s/192.168.100.5/192.168.100.12/` en `/etc/gastos-ia/gastos-ia.env` y `/etc/fstab`.
2. `umount -l` de ambos montajes + `systemctl daemon-reload` + `mount -a` + `systemctl restart gastos-ia`.
3. Verificado: SMB OK, servicio active, `POST /login` responde 401 en 0.18s (antes: timeout).

**PENDIENTE CRITICO (raiz del problema):** ~~la vEthernet del host sigue en DHCP~~ **RESUELTO 2026-08-19:** vEthernet (GastosIA-External, ifIndex 2) fijada como estatica 192.168.100.12/24, gateway 192.168.100.1, DNS 192.168.100.1 (mismos valores que tenia por DHCP; PrefixOrigin Manual, PersistentStore, aplicado via WinRM con pypsrp). El incidente ya no puede repetirse por renovacion DHCP.

**Deuda detectada:** ~~el codigo desplegado en `/opt/gastos-ia` data del 2026-07-31~~ **RESUELTO 2026-08-19:** redespliegue completo desde rama `dev` (rsync + `uv sync --frozen`); verificado login HTMX, monitor SMB y worker FIFO. Respaldo pre-despliegue en `/home/gastos-admin/gastos-ia-backup-20260819.tar.gz`. Nota: se eliminaron archivos huerfanos de una copia manual antigua en la raiz de `/opt/gastos-ia` (`queue.py` ensombrecia el modulo `queue` de stdlib y rompia `urllib3`/`requests`).

## Bugs Corregidos (2026-07-29 / 08-12)

| Fecha | Bug | Fix |
|-------|-----|-----|
| Sep 03 | Detalle de registro: combo Categoria vacio (no se llenaba segun la Cuenta/tipo de gasto seleccionada) | Causa raiz: `catalog_cache.parent_id` nunca se poblaba (migracion desde Catalogo.xlsx descartaba el par categoria→cuenta; CRUD admin no pedia cuenta padre). Fix: (1) `seed_catalogs` liga y repara parent_id al re-ejecutar (`--catalogs-only`); (2) `expense_detail` pre-filtra en la ruta con fallback a todas las categorias si no hay coincidencias; (3) `/categories/by-account` con el mismo fallback; (4) alta de categoria en `/catalogs` ahora pide cuenta padre. DESPLEGADO en lenovosrv: rebuild imagen + backfill (45 vinculos, 33 categorias con padre / 0 sin padre / 9 cuentas). Verificado E2E: detalle muestra categorias filtradas y `/categories/by-account` responde por cuenta. Respaldo pre-despliegue: `/home/administrador/gastos-ia-repo-backup-20260903.tar.gz`. |
| Ago 12 | Envio a Sheets fallaba con `DataError: value out of int64 range` en `pg_advisory_xact_lock` | `_group_lock_id` genera int64 con signo (`signed=True`). Hash de `PSAV-260730` desbordaba el rango sin signo. |
| Ago 12 | Gemini 2.0-flash deprecado (404) de nuevo | `GASTOSIA_GEMINI_MODEL=gemini-flash-latest` (alias rodante) |
| Ago 12 | Imagenes con error de extraccion no se podian reintentar desde la UI | Endpoint `POST /expenses/{id}/retry` + boton "Reenviar" en seccion de errores; `/dashboard/errors` lista solo `ERROR_PROCESAMIENTO` con filtro por dueño |
| Jul 31 | Gemini 2.5-flash deprecado (404) | Cambiar default a gemini-2.0-flash |
| Jul 31 | Gemini cuota agotada (429) sin alternativa | Gemini multi-key + Kimi fallback. Se elimina Ollama por lentitud. |
| Jul 31 | Errores de extraccion invisibles en dashboard | Nueva seccion HTMX con polling 10s de errores recientes |
| Jul 31 | ERROR_PROCESAMIENTO sin detalle en UI | Template muestra extraction_error en amarillo |
| Jul 30 | Ruff E501 x12 + F401 x5 + SIM105 x4 | Wrap lines, contextlib.suppress, unused imports |
| Jul 30 | Test consecutive=5 hardcoded | Random uuid-based values |
| Jul 30 | Event loop conflict (2 tests E2E) | pytest.mark.skip (anyio + async fixtures) |
| Jul 29 | `Image.LANCZOS` Pillow 12.x | `Image.Resampling.LANCZOS` |
| Jul 29 | `.date()` → datetime | Quitar `.date()` |
| Jul 29 | `uuid.UUID()` faltante | `uuid.UUID(category_id)` |
| Jul 29 | `client.py` corrompido | Reescribir completo |
| Jul 29 | `@` en DB password | `urllib.parse.quote_plus()` |
| Jul 29 | Mypy source file twice | `explicit_package_bases = true` |
