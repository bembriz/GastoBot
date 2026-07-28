#!/usr/bin/env python3
"""
Ejemplo de configuracion de Argon2id para Gastos IA.
NO ejecutar directamente - es referencia para app/auth/password.py
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

# Configuracion recomendada para Argon2id (RFC 9106)
# Parametros ajustados para equilibrio seguridad/rendimiento en VM con 4 vCPU
ph = PasswordHasher(
    time_cost=3,        # 3 iteraciones
    memory_cost=65536,  # 64 MB de RAM
    parallelism=4,      # 4 hilos (matching 4 vCPU)
    hash_len=32,        # 32 bytes de hash output
    salt_len=16,        # 16 bytes de salt aleatorio
    encoding='utf-8',
)


def hash_password(password: str) -> str:
    """Genera hash Argon2id de una contrasena."""
    if len(password) < 8:
        raise ValueError("La contrasena debe tener al menos 8 caracteres")
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contrasena contra su hash Argon2id."""
    try:
        return ph.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """Verifica si el hash necesita ser actualizado con parametros mas recientes."""
    try:
        return ph.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


# Ejemplo de uso (NO ejecutar con contrasenas reales versionadas)
if __name__ == "__main__":
    import os

    test_password = "TestPassword123!"
    hashed = hash_password(test_password)
    print(f"Hash generado: {hashed[:50]}...")
    print(f"Formato Argon2id: {hashed.startswith('$argon2id$')}")

    assert verify_password(test_password, hashed), "Verificacion fallida"
    assert not verify_password("WrongPassword", hashed), "Deberia fallar"
    assert not needs_rehash(hashed), "No deberia necesitar rehash"

    print("Todas las pruebas pasaron.")
