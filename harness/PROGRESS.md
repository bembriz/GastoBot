# Progress Tracking — Gastos IA

> Ultima actualizacion: 2026-07-28T22:51:00  

---

## Resumen Global

| Fase | Estado | Progreso | ETA |
|---|---|---|---|
| Fase 0 — Prueba Tecnica | **completed** | 80% | — |
| Fase 1 — Nucleo | **completed** | 100% | — |
| Fase 2 — Interfaz | **completed** | 100% | — |
| Fase 3 — Google Sheets | **completed** | 100% | — |
| Fase 4 — Instalador | **in_progress** | 50% | 10h |
| Fase 5 — Aceptacion | **pending** | 0% | 8h |

---

## Commits (rama `dev`)

```
6c2df6e feat: pipeline integrado - monitor + worker en main.py
f171fbe feat(fase3): integracion Google Sheets completa
93c5cf3 fix(auth): login con HTML+HTMX, redirect HX-Redirect
53075a0 fix(ui): corregir templates con modulo centralizado
89944d6 feat(fase1-2): nucleo e interfaz web completos
9daa657 feat(fase0): completar validacion tecnica
f783f37 feat(arnes): construir arnes completo con 23 skills
```

## Modulos implementados

| Modulo | Archivos |
|---|---|
| `app/database/` | engine, session, models (9 tablas), locking |
| `app/auth/` | password (Argon2id), session, routes, permissions |
| `app/images/` | monitor (SMB 5s, SHA-256, EXIF) |
| `app/expenses/` | routes (dashboard HTMX, visor, update), queue (FIFO), extraction (Ollama) |
| `app/catalogs/` | routes (CRUD categorias/cuentas, solo admin) |
| `app/history/` | routes (busqueda, filtros) |
| `app/sheets/` | client (gspread), tabs (Mes-AA), sender (11 pasos) |
| `templates/` | base, login, dashboard, expense_list, expense_detail, catalogs, history |

## Infraestructura

- **PostgreSQL**: 192.168.100.45:5432, BD `gastos_ia`, usuario `gastos_app`
- **Google Sheets**: "Reporte de gastos 2026", `_Control` con 618 registros
- **Usuarios**: Ruben (admin), Esme (standard) — Argon2id
- **Consecutivos**: 10 grupos (BORAMAR, BUNG, ESTRADOS, OP, PISTANESS, PSAV, STRINGLIGHTS, VAL, VALC, XCARET)

### VM GastosIA (skill-infrastructure completado)
- **Host**: LENOVOSRV (i5-7300HQ, 32 GB, Hyper-V)
- **VM**: 16 GB RAM, 4 vCPU, Gen 2, 120 GB VHDX dynamic
- **OS**: Ubuntu Server 24.04.4 LTS, hostname `gastos-ia`
- **Red**: Static IP `192.168.100.75/24`, gateway `192.168.100.1`
- **SSH**: `gastos-admin@192.168.100.75`
- **Caddy**: HTTPS `gastos.local` → `localhost:8000`
- **Ollama**: `qwen3-vl:4b` (3.3 GB), CPU-only
- **SMB**: `/mnt/smb/Ruben` y `/mnt/smb/Esme` montados (CIFS 3.0)
- **Env**: `/etc/gastos-ia/gastos-ia.env` (0600 root:root)
- **Systemd**: `gastos-ia.service` enabled (pendiente deploy)
- **Auto-start**: VM arranca con host

## Pendiente

- [x] ~~Benchmark Qwen3-VL~~ → realizado al instalar qwen3-vl:4b en VM
- [ ] Fase 4: skill-installer (deploy app, BD, usuarios, Google Sheets, tests)
- [ ] Fase 5: pruebas de aceptacion (39 criterios PRD)
- [ ] Corregir autenticacion asyncpg para `gastos_app` (temp: usando admin)
