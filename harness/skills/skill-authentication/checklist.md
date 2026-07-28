# Checklist — skill-authentication

## Pre-ejecucion
- [ ] `skill-database` completado y tabla `users` existe
- [ ] Columnas requeridas: id, username, password_hash, role, is_active, failed_attempts, locked_until, password_change_required, last_login
- [ ] `uv add argon2-cffi itsdangerous` ejecutado
- [ ] Variables `GASTOSIA_SESSION_SECRET` configurada (>= 32 chars)
- [ ] Variables temporales `GASTOSIA_RUBEN_INITIAL_PASSWORD` y `GASTOSIA_ESME_INITIAL_PASSWORD` disponibles
- [ ] Rama `arnes` activa

## Ejecucion — Argon2id
- [ ] `app/auth/password.py` creado con `argon2.PasswordHasher`
- [ ] Parametros: time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16
- [ ] `hash_password()` retorna string con prefijo `$argon2id$`
- [ ] `verify_password()` maneja `VerifyMismatchError`
- [ ] `needs_rehash()` implementado
- [ ] NO usa passlib, bcrypt, SHA, MD5

## Ejecucion — Usuarios iniciales
- [ ] `scripts/init_users.py` creado
- [ ] Lee contrasenas de variables de entorno (NO de argumentos CLI)
- [ ] Valida longitud minima 8 caracteres
- [ ] Genera hash Argon2id
- [ ] INSERT ON CONFLICT para idempotencia
- [ ] Ruben: role=admin, password_change_required=True
- [ ] Esme: role=standard, password_change_required=True
- [ ] NO loguea contrasenas en ningun output
- [ ] Verificado en BD: `SELECT username, role, password_change_required FROM users`

## Ejecucion — Sesiones
- [ ] `app/auth/session.py` creado
- [ ] Usa `itsdangerous.URLSafeTimedSerializer` con `GASTOSIA_SESSION_SECRET`
- [ ] Duracion: 8 horas (configurable)
- [ ] `create_session()` retorna token firmado
- [ ] `verify_session()` verifica firma y expiracion
- [ ] `get_current_user` dependency lee cookie `gastosia_session`

## Ejecucion — Endpoints
- [ ] POST /login: recibe username+password, verifica hash
- [ ] POST /login: incrementa failed_attempts en fallo
- [ ] POST /login: bloquea 15 min tras 5 fallos (423 Locked)
- [ ] POST /login: resetea failed_attempts en exito
- [ ] POST /login: actualiza last_login
- [ ] POST /login: setea cookie HttpOnly, Secure, SameSite=Strict
- [ ] POST /login: retorna password_change_required
- [ ] POST /logout: elimina cookie
- [ ] POST /change-password: verifica current, guarda nuevo hash
- [ ] POST /change-password: password_change_required = False
- [ ] GET /api/me: retorna usuario sin hash

## Ejecucion — RBAC
- [ ] `require_admin` dependency: 403 si role != admin
- [ ] `require_owner_or_admin`: 403 si no es owner ni admin
- [ ] Rutas `/catalogs/*` protegidas con `require_admin`
- [ ] Rutas `/expenses/*` protegidas con `require_owner_or_admin`
- [ ] Esme no puede ver gastos de Ruben
- [ ] Ruben puede ver todos los gastos

## Ejecucion — Pruebas
- [ ] `scripts/validation/test_authentication.py` ejecutado
- [ ] Login exitoso -> 200 + cookie
- [ ] Login fallido -> 401 + intentos restantes
- [ ] 5 fallos -> bloqueo 15 min (423)
- [ ] Sin sesion -> 302/401 en rutas protegidas
- [ ] Standard en ruta admin -> 403
- [ ] Cambio de contrasena funcional
- [ ] Hash es Argon2id (regex)

## Post-ejecucion
- [ ] Evidencia `sistema-autenticacion.json` generada
- [ ] Evidencia `sistema-autenticacion.md` generada
- [ ] `skill-quality-gate` ejecutado
- [ ] Contrasenas iniciales eliminadas del entorno
- [ ] `harness/PROGRESS.md` actualizado
