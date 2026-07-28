# Checklist — skill-fase0-tecnica

## Pre-ejecucion
- [ ] Rama `arnes` activa y sin cambios sin commitear
- [ ] PRD v1.2 presente en `docs/PRD_Gastos_IA_v1_2.md`
- [ ] AGENTS.md cargado con `fase0.status == "pending"`
- [ ] Directorio `ejemplos/` contiene >= 50 imagenes (.jpg, .jpeg, .png, .webp)
- [ ] Ollama instalado y respondiendo (`ollama --version`)
- [ ] PostgreSQL accesible desde el entorno de ejecucion
- [ ] Archivo JSON de cuenta de servicio Google disponible (ruta en variable de entorno)
- [ ] `uv` instalado y funcional (`uv --version`)
- [ ] Directorio `harness/evidence/fase0/` existe (crear si no)
- [ ] `.env.example` existe en la raiz del proyecto
- [ ] Scripts de validacion NO contienen secretos hardcodeados

## Ejecucion
- [ ] Fase 0 cambiada a `in_progress` en AGENTS.md
- [ ] `harness/PROGRESS.md` actualizado con ETA inicial
- [ ] `.env.example` validado: 14 variables, sin valores reales
- [ ] Script `validate_secrets.py` ejecutado exitosamente
- [ ] Conexion a PostgreSQL establecida y verificada
- [ ] Base `gastos_ia` y usuario `gastos_app` creados
- [ ] Permisos otorgados correctamente
- [ ] Google Sheets API: autenticacion exitosa
- [ ] Google Sheets API: lectura de pestañas existentes
- [ ] Google Sheets API: escritura y eliminacion de pestaña de prueba
- [ ] Datos historicos cargados a `_Control` (si aplica)
- [ ] Consecutivos maximos calculados por grupo
- [ ] Duplicados en historicos detectados y reportados
- [ ] Ambos modelos Qwen3-VL (2B, 4B) disponibles en Ollama
- [ ] Benchmark ejecutado sobre >= 50 imagenes con ambos modelos
- [ ] Tiempos de inferencia registrados por imagen y modelo
- [ ] Consumo de RAM registrado durante inferencia
- [ ] JSON de respuesta validado estructuralmente para cada inferencia
- [ ] Metricas agregadas calculadas (exactitud, % JSON valido, tiempo promedio)
- [ ] Modelo recomendado segun resultados vs umbrales PRD §32
- [ ] Ningun secreto expuesto en logs, stdout, o archivos de evidencia

## Post-ejecucion
- [ ] 10 archivos de evidencia generados en `harness/evidence/fase0/`
- [ ] Evidencia JSON valida contra `harness/config/schemas/evidence.schema.json`
- [ ] Evidencia MD sigue `harness/config/schemas/evidence-markdown.schema.md`
- [ ] `skill-quality-gate` ejecutado exitosamente
- [ ] Fase 0 marcada como `completed` en AGENTS.md
- [ ] `harness/PROGRESS.md` actualizado con resumen final
- [ ] Resumen ejecutivo presentado al usuario
- [ ] GATE manual solicitado para avanzar a Fase 1
- [ ] `.env` de prueba en `/tmp/` eliminado
- [ ] Pestaña `_Test_Fase0` eliminada de Google Sheets
