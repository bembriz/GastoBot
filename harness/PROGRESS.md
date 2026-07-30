# Progress Tracking — Gastos IA

> Ultima actualizacion: 2026-07-29T20:08:00
> Estado: MVPS completado (Fases 0-5). Sistema operativo en https://gastos.local.
> Pendiente: pruebas manuales de concurrencia/reinicio con imagenes reales.  

---

## Resumen Global

| Fase | Estado | Progreso | ETA |
|---|---|---|---|
| Fase 0 — Prueba Tecnica | **completed** | 80% | — |
| Fase 1 — Nucleo | **completed** | 100% | — |
| Fase 2 — Interfaz | **completed** | 100% | — |
| Fase 3 — Google Sheets | **completed** | 100% | — |
| Fase 4 — Instalador | **completed** | 100% | — |
| Fase 5 — Aceptacion | **completed** | 85% | — |

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

- [x] ~~Fase 4: skill-installer~~ → app desplegada, BD configurada, Google Sheets operativo, servicios activos
- [x] ~~Bug: @ en password BD rompia URL asyncpg~~ → fix con quote_plus en engine.py
- [x] ~~Bug: session cookie y HX-Redirect no se enviaban~~ → fix: setear headers en HTMLResponse retornado
- [x] ~~Bug: monitor pisaba status LISTO_PARA_REVISION con DUPLICADO_EXACTO~~ → fix: solo marcar si status=DETECTADO
- [x] ~~Bug: OCR lento (Ollama CPU 5+ min)~~ → reemplazado por Gemini Flash (~2s)
- [x] ~~Catálogos: cuentas + categorías dependientes~~ → parent_id + HTMX filter
- [x] ~~Dashboard: tabla con checkboxes + bulk send a Sheets~~ → implementado con persistencia JS
- [ ] Fase 5: pruebas de aceptacion (39 criterios PRD)
- [ ] Crear tests unitarios y E2E
- [ ] Manual operativo para usuarios

## Bugs Corregidos (Fase 4)

| Bug | Archivo | Fix |
|-----|---------|-----|
| `@` en DB password rompe asyncpg | `app/database/engine.py:1` | `urllib.parse.quote_plus()` en DB_USER y DB_PASS |
| Session cookie y HX-Redirect no se envian | `app/auth/routes.py:83-93` | setear headers/cookies en el HTMLResponse retornado |
