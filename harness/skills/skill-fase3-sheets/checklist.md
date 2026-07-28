# Checklist — skill-fase3-sheets

## Pre-ejecución
- [ ] Fase 2 status es `completed` en AGENTS.md
- [ ] Todos los artefactos de Fase 2 existen en `harness/evidence/fase2/`
- [ ] Catálogos (categorías y cuentas) poblados en PostgreSQL
- [ ] Registros en estado LISTO_PARA_REVISION o REQUIERE_REVISION disponibles
- [ ] GASTOSIA_GOOGLE_CREDENTIALS_PATH configurado y archivo JSON existe
- [ ] GASTOSIA_GOOGLE_SPREADSHEET_ID configurado
- [ ] Cuenta de servicio con acceso de editor al spreadsheet
- [ ] Google Sheets API habilitada
- [ ] `uv sync --frozen` exitoso
- [ ] Branch `arnes` activa

## Ejecución
- [ ] `skill-google-sheets` invocado y completado con éxito
- [ ] Evidencia `integracion-sheets.json` generada
- [ ] Evidencia `integracion-sheets.md` generada
- [ ] Sincronización de catálogos desde _Categorias y _Cuentas
- [ ] Pestañas mensuales con 16 encabezados creadas
- [ ] _Control sheet con campos mínimos
- [ ] Asignación de consecutivos por grupo
- [ ] Inserción de nuevos registros
- [ ] Actualización de registros existentes
- [ ] Movimiento entre meses
- [ ] Cola offline (PENDIENTE_DE_ENVIO)
- [ ] Conciliación con _Control
- [ ] `skill-quality-gate` ejecutado para Fase 3
- [ ] Todas las verificaciones de quality gate pasan
- [ ] Reporte de fase `fase3-summary.json` generado
- [ ] Reporte de fase `fase3-summary.md` generado

## Post-ejecución
- [ ] Los 4 archivos de evidencia existen en `harness/evidence/fase3/`
- [ ] `fase3.status` cambiado a `completed` en AGENTS.md
- [ ] `harness/PROGRESS.md` actualizado
- [ ] Resumen ejecutivo presentado al usuario
- [ ] GATE manual solicitado para Fase 4
- [ ] No hay secretos en el diff
- [ ] Cobertura de tests >= 90%
- [ ] Envío a Sheets funcional con registros reales
- [ ] Offline mode verificado (sin internet, registro queda PENDIENTE_DE_ENVIO)
