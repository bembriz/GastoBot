# Evidence Report — skill-authentication

> **Skill:** `skill-authentication`
> **Fase:** `fase1`
> **Timestamp:** `{iso8601}`
> **Estado:** `[PASADO | FALLADO | PARCIAL]`
> **Duracion:** `{duration}`

---

## Resumen Ejecutivo

{Summary: Argon2id configured, users created, session management implemented, rate limiting tested, RBAC working.}

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | {N} |
| Pasadas | {N} |
| Fallidas | {N} |
| Algoritmo hash | Argon2id |
| Usuarios creados | 2 (Ruben admin, Esme standard) |
| Duracion sesion | 28800s (8h) |
| Intentos maximos | 5 |
| Tiempo bloqueo | 900s (15min) |
| Errores | {N} |
| Advertencias | {N} |

---

## Verificaciones

### Pre-ejecucion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Tabla `users` existe | {status} | {N} columnas |
| C2 | Dependencias instaladas | {status} | argon2-cffi, itsdangerous |
| C3 | `GASTOSIA_SESSION_SECRET` configurada | {status} | {len} caracteres |

### Ejecucion — Configuracion

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Argon2id PasswordHasher configurado | {status} | time_cost=3, memory=64MB |
| C2 | `hash_password()` funcional | {status} | Prefijo `$argon2id$` |
| C3 | `verify_password()` funcional | {status} | Maneja VerifyMismatchError |
| C4 | `needs_rehash()` funcional | {status} | {detail} |

### Ejecucion — Usuarios

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Ruben creado (admin) | {status} | password_change_required=True |
| C2 | Esme creada (standard) | {status} | password_change_required=True |
| C3 | Hash almacenado en BD (no texto plano) | {status} | Formato Argon2id |
| C4 | Contrasenas iniciales NO persistidas | {status} | Variables eliminadas |

### Ejecucion — Sesiones

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | `create_session()` genera token | {status} | URLSafeTimedSerializer |
| C2 | `verify_session()` valida token | {status} | Firma + expiracion |
| C3 | Cookie HttpOnly | {status} | {detail} |
| C4 | Cookie Secure | {status} | {detail} |
| C5 | Cookie SameSite=Strict | {status} | {detail} |

### Ejecucion — Endpoints

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | POST /login exito | {status} | 200 + cookie |
| C2 | POST /login fallo | {status} | 401 + intentos restantes |
| C3 | POST /login bloqueo | {status} | 423 tras 5 fallos |
| C4 | POST /login desbloqueo | {status} | Tras 15 min, login OK |
| C5 | POST /logout | {status} | Cookie eliminada |
| C6 | POST /change-password | {status} | Hash actualizado |
| C7 | GET /api/me | {status} | Datos usuario sin hash |

### Ejecucion — RBAC

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Admin accede a /catalogs | {status} | 200 |
| C2 | Standard a /catalogs | {status} | 403 |
| C3 | Owner accede a su gasto | {status} | 200 |
| C4 | Standard accede a gasto ajeno | {status} | 403 |
| C5 | Admin accede a gasto ajeno | {status} | 200 |

---

## Artefactos Generados

| Archivo | Tipo | Descripcion |
|---|---|---|
| `app/auth/password.py` | source | Argon2id hashing |
| `app/auth/session.py` | source | Sesiones firmadas |
| `app/auth/routes.py` | source | Endpoints auth |
| `app/auth/permissions.py` | source | RBAC dependencies |
| `scripts/init_users.py` | script | Creacion inicial de usuarios |
| `scripts/validation/test_authentication.py` | script | Pruebas de autenticacion |
| `harness/evidence/fase1/sistema-autenticacion.json` | report | Evidencia JSON |
| `harness/evidence/fase1/sistema-autenticacion.md` | report | Evidencia Markdown |

---

## Errores (si los hay)

| Codigo | Mensaje |
|---|---|
| `ERR_XXX` | {description} |

---

## Advertencias (si las hay)

- {warning}

---

## Proximos Pasos

1. Proceder con `skill-folder-monitor`
2. Configurar variables de entorno permanentes (sin contrasenas iniciales)
3. Verificar que Caddy sirve cookies Secure correctamente

---

## Precondiciones al Inicio

```json
{
  "database_skill_completed": true,
  "users_table_exists": true,
  "argon2_cffi_installed": true,
  "session_secret_length": {N},
  "init_passwords_provided": true
}
```

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
