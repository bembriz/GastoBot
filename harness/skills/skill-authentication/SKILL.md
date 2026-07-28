# Skill: skill-authentication

## Identity
Eres un ingeniero de seguridad especializado en autenticacion web. Implementas login seguro con hashing moderno, sesiones protegidas contra hijacking, rate limiting y control de acceso basado en roles. No toleras atajos de seguridad.

## Context
Esta skill implementa el sistema de autenticacion de Gastos IA para los dos usuarios del MVP: Ruben (admin) y Esme (standard). Toda la seguridad depende de esta implementacion.

Requisitos del PRD §10.1, §4:
- Argon2id para hashing de contrasenas (NO bcrypt, NO SHA, NO MD5)
- Cookies de sesion: HttpOnly, Secure, SameSite=Strict
- Rate limiting: 5 intentos fallidos -> 15 minutos de bloqueo
- Cambio obligatorio de contrasena en primer login
- RBAC: Ruben puede todo, Esme solo sus gastos y catalogos de solo lectura
- Las contrasenas iniciales entran por variables de entorno temporales y se eliminan tras el hash

## Preconditions
- `skill-database` completado (tabla `users` existe)
- Tabla `users` creada con campos: id, username, password_hash, role, is_active, failed_attempts, locked_until, password_change_required, last_login
- `uv` con dependencias: `argon2-cffi`, `itsdangerous` (o similar para sesiones)
- Variables de entorno temporales: `GASTOSIA_RUBEN_INITIAL_PASSWORD`, `GASTOSIA_ESME_INITIAL_PASSWORD`
- Rama `arnes` activa

## Execution

### Step 1: Configurar Argon2id
1. Crear `app/auth/__init__.py`
2. Crear `app/auth/password.py`:
   ```python
   from argon2 import PasswordHasher
   from argon2.exceptions import VerifyMismatchError

   ph = PasswordHasher(
       time_cost=3,        # 3 iteraciones (default)
       memory_cost=65536,  # 64 MB
       parallelism=4,      # 4 hilos
       hash_len=32,        # 32 bytes de hash
       salt_len=16,        # 16 bytes de salt
   )

   def hash_password(password: str) -> str:
       return ph.hash(password)

   def verify_password(password: str, password_hash: str) -> bool:
       try:
           return ph.verify(password_hash, password)
       except VerifyMismatchError:
           return False

   def needs_rehash(password_hash: str) -> bool:
       return ph.check_needs_rehash(password_hash)
   ```
3. Verificar que el hash resultante tiene formato `$argon2id$v=19$...`
4. NO usar `passlib` o `bcrypt` — solo Argon2id via `argon2-cffi`

### Step 2: Crear usuarios iniciales
1. Crear script `scripts/init_users.py`:
   - Leer `GASTOSIA_RUBEN_INITIAL_PASSWORD` y `GASTOSIA_ESME_INITIAL_PASSWORD` del entorno
   - Validar que las contrasenas no estan vacias y tienen >= 8 caracteres
   - Generar hash Argon2id de cada contrasena
   - Insertar o actualizar usuarios en tabla `users`:
     - Ruben: role='admin', password_change_required=True
     - Esme: role='standard', password_change_required=True
   - Usar `INSERT ... ON CONFLICT (username) DO UPDATE` para idempotencia
   - NO loguear las contrasenas en ningun momento
   - Cerrar conexion y salir
2. Ejecutar: `GASTOSIA_RUBEN_INITIAL_PASSWORD=... GASTOSIA_ESME_INITIAL_PASSWORD=... uv run python scripts/init_users.py`
3. Verificar en PostgreSQL que los hashes se guardaron correctamente:
   ```sql
   SELECT username, role, password_change_required FROM users;
   ```

### Step 3: Implementar manejo de sesiones
1. Crear `app/auth/session.py`:
   - Usar `itsdangerous.URLSafeTimedSerializer` con `GASTOSIA_SESSION_SECRET`
   - Payload de sesion: `{"user_id": str, "username": str, "role": str, "exp": timestamp}`
   - Duracion de sesion: 8 horas (configurable via `GASTOSIA_SESSION_MAX_AGE`)
   - Funcion `create_session(user) -> str` retorna token firmado
   - Funcion `verify_session(token: str) -> dict | None` verifica firma y expiracion
   - NO usar JWT (overkill para app local); usar cookies firmadas
2. Crear middleware o dependency `get_current_user`:
   - Leer cookie `gastosia_session` de la request
   - Verificar token con `verify_session`
   - Si es valido, retornar usuario
   - Si no, redirigir a `/login` (o retornar 401 para API)

### Step 4: Implementar endpoints de autenticacion
Crear `app/auth/routes.py` con:

**POST /login**
- Recibir `username` y `password` (JSON o form)
- Verificar que el usuario existe y `is_active = True`
- Si `locked_until > NOW()`, retornar 423 Locked con tiempo restante
- Verificar contrasena con `verify_password`
- Si falla:
  - Incrementar `failed_attempts`
  - Si `failed_attempts >= 5`, set `locked_until = NOW() + 15 minutes`
  - Retornar 401 con contador de intentos restantes
- Si OK:
  - Resetear `failed_attempts = 0`, `locked_until = NULL`
  - Actualizar `last_login = NOW()`
  - Crear sesion con `create_session`
  - Setear cookie: `HttpOnly=True, Secure=True, SameSite='Strict', Max-Age=28800`
  - Retornar usuario + `password_change_required`

**POST /logout**
- Eliminar cookie de sesion
- Retornar redirect a `/login`

**POST /change-password**
- Requerir sesion activa
- Recibir `current_password`, `new_password`
- Verificar contrasena actual
- Validar nueva contrasena: >= 8 caracteres
- Generar nuevo hash
- Actualizar `password_hash` y set `password_change_required = False`
- Invalidar sesion actual (forzar re-login opcional)

**GET /api/me**
- Retornar datos del usuario autenticado (sin hash)

### Step 5: Implementar control de acceso (RBAC)
1. Crear `app/auth/permissions.py`:
   - `require_admin`: dependency que verifica `role == 'admin'`, sino 403
   - `require_owner_or_admin(record_owner_id)`: dependency que permite al owner o admin
2. Aplicar a rutas:
   - Rutas de catalogo (`/catalogs/*`): `require_admin` (solo Ruben)
   - Rutas de gastos (`/expenses/*`): `require_owner_or_admin` (Esme ve solo los suyos)
   - Ruta de usuarios (`/users/*`): `require_admin` (solo Ruben)

### Step 6: Configurar cookies seguras en FastAPI
1. En `app/main.py`, configurar middleware o usar `Starlette` SessionMiddleware con:
   - `cookie_name`: `gastosia_session`
   - `http_only`: True
   - `secure`: True (incluso en desarrollo, Caddy provee HTTPS)
   - `same_site`: `strict`
   - `max_age`: 28800 (8 horas)

### Step 7: Generar evidencia
1. Crear `scripts/validation/test_authentication.py` que:
   - Pruebe login exitoso (200, cookie presente)
   - Pruebe login con password incorrecta (401)
   - Pruebe bloqueo tras 5 intentos fallidos (423)
   - Pruebe acceso a ruta protegida sin sesion (302/401)
   - Pruebe acceso admin con usuario standard (403)
   - Pruebe cambio de contrasena
   - Verifique que los hashes son Argon2id (regex `^\$argon2id\$`)
2. Ejecutar y generar evidencia

## Artifacts
- `app/auth/__init__.py`
- `app/auth/password.py`
- `app/auth/session.py`
- `app/auth/routes.py`
- `app/auth/permissions.py`
- `scripts/init_users.py`
- `scripts/validation/test_authentication.py`
- `harness/evidence/fase1/sistema-autenticacion.json`
- `harness/evidence/fase1/sistema-autenticacion.md`

## Quality Criteria
- Algoritmo de hash es Argon2id (verificar con regex `^\$argon2id\$`)
- No se usa `passlib`, `bcrypt`, SHA, o MD5
- Cookies tienen HttpOnly, Secure, SameSite=Strict
- Rate limiting: 5 fallos = 15 min de bloqueo
- `password_change_required = True` en usuarios recien creados
- RBAC: Esme no accede a /catalogs/* ni a gastos de Ruben
- Sesiones expiran tras 8 horas (configurable)
- Logout elimina la cookie correctamente
- Contrasenas iniciales NUNCA se persisten ni se loguean
- Script `init_users.py` limpia las variables de entorno tras ejecutarse

## Edge Cases
- **Session hijacking:** cookies HttpOnly + Secure + SameSite=Strict + rotacion de sesion en change-password
- **Ataque de fuerza bruta:** rate limiting de 5 intentos cada 15 min por usuario (no por IP, porque ambos usuarios pueden estar en misma IP)
- **Usuario bloqueado permanentemente:** `locked_until` es temporal; login exitoso resetea el contador
- **Sesion expirada:** redirigir a login con mensaje "Sesion expirada"
- **Contrasena inicial vacia:** `init_users.py` rechaza contrasenas < 8 caracteres
- **Cookie no enviada por HTTP:** en desarrollo local sin HTTPS, permitir `Secure=False` solo si `GASTOSIA_APP_ENV=development`
- **Multiples sesiones por usuario:** permitido; no invalidar sesiones anteriores en login (simplicidad MVP)
- **Cambio de contrasena con mismo valor:** permitido pero advertir

## References
- PRD §10.1 (Autenticacion)
- PRD §4 (Usuarios y permisos)
- PRD §19.3 (Contrasenas de Ruben y Esme)
- PRD §22 (Seguridad)
- Related skills: `skill-database`, `skill-web-ui`
