#!/usr/bin/env python3
"""
Ejemplo de como invocar secuencialmente los sub-skills de Fase 1.

Este script es una REFERENCIA para el orquestador, no se ejecuta directamente.
El arnes de OpenCode invoca cada skill via el mecanismo de skills.
"""

# Flujo conceptual de Fase 1:
#
# 1. skill-database
#    - Crear tablas: users, expense_records, image_files, extraction_runs,
#      processing_queue, catalog_cache, sheet_sync, audit_events, system_settings
#    - Ejecutar migraciones con Alembic
#    - Verificar indices y constraints
#
# 2. skill-authentication
#    - Implementar /login, /logout, /change-password
#    - Configurar Argon2id con salt aleatorio
#    - Crear middleware de sesion con cookies seguras
#    - Implementar rate limiting (5 intentos -> 15min)
#    - Crear usuarios iniciales Ruben y Esme
#
# 3. skill-folder-monitor
#    - Montar carpetas SMB
#    - Iniciar bucle de monitoreo (cada 5s)
#    - Validar estabilidad de archivos
#    - Calcular SHA-256
#    - Corregir orientacion EXIF
#    - Insertar en image_files y encolar en processing_queue
#
# 4. skill-fifo-queue
#    - Implementar worker unico con advisory lock
#    - Reclamar siguiente trabajo con SELECT FOR UPDATE SKIP LOCKED
#    - Transiciones de estado: EN_COLA -> ANALIZANDO -> LISTO/ERROR
#    - Recuperacion de trabajos ANALIZANDO tras reinicio
#
# 5. skill-image-extraction
#    - Enviar imagen a Ollama con prompt estructurado
#    - Parsear y validar JSON de respuesta
#    - Normalizar campos (fecha ISO, monto float)
#    - Calcular y almacenar confianza por campo
#    - Insertar en extraction_runs
#    - Actualizar expense_records con datos extraidos

print("Este archivo es una referencia conceptual. No se ejecuta directamente.")
print("El orquestador invoca cada skill a traves del mecanismo de skills de OpenCode.")
