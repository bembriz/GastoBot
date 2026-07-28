# Checklist — skill-fase2-interfaz

## Pre-ejecución
- [ ] Fase 1 status es `completed` en AGENTS.md
- [ ] Todos los artefactos de Fase 1 existen en `harness/evidence/fase1/`
- [ ] `uv sync --frozen` ejecuta sin errores
- [ ] PostgreSQL está accesible y las migraciones están aplicadas
- [ ] La aplicación FastAPI arranca sin errores
- [ ] Branch `arnes` está activa

## Ejecución
- [ ] `skill-web-ui` invocado y completado con éxito
- [ ] Evidencia `interfaz-web.json` y `interfaz-web.md` generada
- [ ] `skill-catalogs` invocado y completado con éxito
- [ ] Evidencia `catalogos.json` y `catalogos.md` generada
- [ ] `skill-history` invocado y completado con éxito
- [ ] Evidencia `historial.json` y `historial.md` generada
- [ ] `skill-quality-gate` ejecutado para Fase 2
- [ ] Todas las verificaciones de quality gate pasan
- [ ] Reporte de fase `fase2-summary.json` generado
- [ ] Reporte de fase `fase2-summary.md` generado

## Post-ejecución
- [ ] Los 8 archivos de evidencia existen en `harness/evidence/fase2/`
- [ ] `fase2.status` cambiado a `completed` en AGENTS.md
- [ ] `harness/PROGRESS.md` actualizado
- [ ] Resumen ejecutivo presentado al usuario
- [ ] GATE manual solicitado para fase 3
- [ ] No hay secretos en el diff
- [ ] Cobertura de tests >= 90%
- [ ] Ambos roles (Ruben/Esme) verificados funcionalmente
- [ ] HTMX polling verificado: transiciones EN_COLA→ANALIZANDO→LISTO_PARA_REVISION
