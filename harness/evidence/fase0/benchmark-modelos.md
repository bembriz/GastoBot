# Evidence Report — Benchmark de Modelos

> **Skill:** `skill-fase0-tecnica`  
> **Fase:** `fase0`  
> **Timestamp:** `2026-07-28T12:30:00Z`  
> **Estado:** BLOQUEADO  

---

## Resumen Ejecutivo

Benchmark de Qwen3-VL (2B vs 4B) bloqueado: Ollama no está instalado en este entorno. El script `benchmark_modelos.py` está listo con todas las funcionalidades requeridas. Se ejecutará sobre las 92 imágenes reales de `ejemplos/`.

---

## Script disponible

```bash
# Instalar Ollama primero:
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3-vl:2b
ollama pull qwen3-vl:4b

# Ejecutar benchmark (completo: ~2-4 horas con 92 imágenes x 2 modelos):
python scripts/validation/benchmark_modelos.py

# Modo rápido (25 imágenes):
python scripts/validation/benchmark_modelos.py --quick

# Solo un modelo:
python scripts/validation/benchmark_modelos.py --model 4b
```

### Funcionalidades:
- Envío de imágenes base64 a API de Ollama
- Prompt estructurado según PRD §7.2
- Parseo robusto de JSON con limpieza de markdown
- Validación de 5 campos requeridos + tipos
- Métricas: tiempo encode, tiempo inferencia, % JSON válido
- Métricas agregadas por modelo
- Salida JSON detallada + resumen en consola
- Soporte para `--quick` (25 imágenes) y `--model` (2b|4b)

### Criterios de comparación (PRD §7.1):
- Exactitud de montos
- Exactitud de fechas
- Identificación de bancos
- Clasificación de transacción
- Descripción del gasto
- JSON válido
- Tiempo de procesamiento
- Consumo de RAM

---

## Bloqueante

Ollama no instalado. Acciones:
1. Instalar Ollama en VM Ubuntu: `curl -fsSL https://ollama.com/install.sh | sh`
2. Verificar instalación: `ollama --version`
3. Descargar modelos: `ollama pull qwen3-vl:2b && ollama pull qwen3-vl:4b`
4. Verificar con: `ollama list | grep qwen3-vl`

---

*Reporte generado por el arnés Gastos IA v1.0*
