# Skill: skill-kimi-integration

## Identity
Eres un ingeniero de integracion de APIs especializado en modelos de lenguaje. Integras Kimi API (Moonshot AI) como motor de extraccion multimodal en el pipeline de Gastos IA. Conoces a fondo los modelos Kimi, sus parametros, restricciones y estructura de precios.

## Context
Esta skill documenta la integracion con Kimi API como motor de fallback para extraccion de tickets. Kimi es un API de pago compatible con OpenAI que ofrece modelos multimodales con soporte de vision (imagen y video). Se usa cuando las keys gratuitas de Gemini se quedan sin cuota.

Requisitos del PRD:
- Extraccion multimodal de comprobantes bancarios mexicanos
- 5 campos requeridos: transaction_date, amount, ticket_description, bank, transaction_type
- Formato JSON estructurado

## Preconditions
- Cuenta en [Kimi Platform](https://platform.kimi.ai/) con API Key activa
- Variable `GASTOSIA_KIMI_API_KEY` configurada en `.envrc` y VM `/etc/gastos-ia/gastos-ia.env`
- Variable `GASTOSIA_KIMI_MODEL` configurada (default: `kimi-k2.6`)
- Dependencia `httpx` instalada (ya incluida en el proyecto)
- `skill-image-extraction` completado (pipeline de extraccion existe)
- Rama `arnes` activa

## Modelos Kimi Disponibles

| Modelo | Contexto | Vision | Temperatura | Thinking | Descripcion |
|--------|----------|--------|-------------|----------|-------------|
| `kimi-k3` | 1M | Si | Fija 1.0 | Siempre | Flagship, el mas capaz. Usa `reasoning_effort` (low/high/max) |
| `kimi-k2.7-code-highspeed` | 256K | Si | Fija 1.0 | Siempre | Enfocado a codigo, alta velocidad (~180 tok/s) |
| `kimi-k2.6` | 256K | Si | 1.0/0.6* | Configurable | Proposito general, thinking on/off |
| `moonshot-v1-8k-vision-preview` | 8K | Si | 0.0 (modificable) | No | **Deprecado**. No usar en nuevos proyectos |

\* kimi-k2.6: temperatura 1.0 en thinking mode, 0.6 en non-thinking mode. Fija, no modificable.

### Notas criticas sobre parametros

**TODOS los modelos Kimi (k3, k2.7, k2.6) tienen parametros FIJOS:**
- `temperature`: Fijo. No enviar. Cualquier valor != default causa error 400.
- `top_p`: Fijo a 0.95. No enviar.
- `n`: Fijo a 1. No enviar.
- `presence_penalty` / `frequency_penalty`: Fijos a 0. No enviar.
- `max_tokens`: Opcional, default 32K.
- `thinking`: Solo k2.6/k2.5. `{"type": "enabled"}` (default) o `{"type": "disabled"}`.

**Regla de oro: NO enviar `temperature`, `top_p`, `n`, `presence_penalty`, `frequency_penalty`. Usar solo `model` + `messages`.**

## API Reference

### Base URL
```
https://api.moonshot.ai/v1
```

### Chat Completions Endpoint
```
POST https://api.moonshot.ai/v1/chat/completions
```

### Autenticacion
```
Authorization: Bearer $MOONSHOT_API_KEY
```

### Vision Input (imagen base64)
```json
{
  "model": "kimi-k2.6",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,<base64_data>"
          }
        },
        {
          "type": "text",
          "text": "Describe esta imagen."
        }
      ]
    }
  ]
}
```

### Formatos de imagen soportados
- image/jpeg, image/png, image/gif, image/webp, image/bmp, image/heic, image/heif
- Maximo recomendado: 4K (4096x2160)
- Tamaño maximo del request body: 100MB

### Errores comunes

| HTTP | Error | Causa | Solucion |
|------|-------|-------|----------|
| 400 | `invalid_request_error` | Parametro invalido (ej. temperature != default) | No enviar parametros fijos |
| 400 | `invalid_request_error` | Modelo no valido | Verificar nombre del modelo |
| 401 | `authentication_error` | API Key invalida | Verificar `MOONSHOT_API_KEY` |
| 404 | `resource_not_found_error` | Modelo deprecado/no existe | Usar modelo actual (kimi-k2.6, kimi-k3) |
| 429 | `rate_limit_error` | Rate limit excedido | Esperar o reducir frecuencia |
| 500 | `server_error` | Error interno Kimi | Reintentar con backoff |

## Implementacion en Gastos IA

### Archivo: `app/expenses/extraction.py`

La funcion `_kimi_extract` usa httpx para llamar al API:

```python
async def _kimi_extract(image_path: str, mime: str) -> dict[str, Any]:
    import httpx

    with open(image_path, "rb") as f:
        image_data = f.read()

    encoded = base64.b64encode(image_data).decode("utf-8")
    data_url = f"data:{mime};base64,{encoded}"

    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": KIMI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": PROMPT_EXTRACCION},
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(KIMI_BASE, headers=headers, json=body)

    if resp.status_code != 200:
        return {
            "raw_response": "",
            "engine": "kimi",
            "error_message": f"Kimi error {resp.status_code}: {resp.text[:200]}",
        }

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return {
        "raw_response": content,
        "engine": "kimi",
        "error_message": None,
    }
```

### Pipeline de extraccion

El orden de fallback es:
1. Gemini key 1 (bembriz)
2. Gemini key 2 (xuum23)
3. Kimi (kimi-k2.6)

Si todas las Gemini fallan (RESOURCE_EXHAUSTED / 429), se usa Kimi automaticamente.
Si Kimi tambien falla, el registro queda como ERROR_PROCESAMIENTO y el error es visible en
la seccion de errores del dashboard.

### Variables de entorno requeridas

| Variable | Descripcion | Default | Requerida |
|----------|-------------|---------|-----------|
| `GASTOSIA_KIMI_API_KEY` | API Key de Kimi/Moonshot | - | Si |
| `GASTOSIA_KIMI_MODEL` | Modelo a usar | `kimi-k2.6` | No |

## Costos

Kimi cobra por token (input + output). Los modelos de vision consumen tokens segun resolucion de imagen.

- Consola de billing: https://platform.kimi.ai/console/billing
- Precios actualizados: https://platform.kimi.ai/docs/pricing/chat-k26
- Estimacion de tokens: POST /v1/estimate-token-count

### Recomendacion para control de costos
- Usar `kimi-k2.6` con thinking deshabilitado para extraccion simple
- Redimensionar imagenes a max 2048px en el lado mas largo (ya lo hace el monitor)
- Monitorear uso en la consola de Kimi

## Actualizacion de modelos

### Si un modelo devuelve 404 (deprecado)

1. Consultar modelos actuales: https://platform.kimi.ai/docs/models
2. Verificar parametros del nuevo modelo: https://platform.kimi.ai/docs/api/models-overview
3. Actualizar `GASTOSIA_KIMI_MODEL` en .env y en la VM
4. **NO enviar temperature ni otros parametros fijos** - todos los modelos Kimi nuevos tienen parametros fijos
5. Probar con una imagen real
6. Desplegar a la VM

### Modelos deprecados (NO USAR)

- `moonshot-v1-8k-vision-preview` y toda la serie `moonshot-v1-*-vision-preview` (sunset Agosto 2026)
- Serie `kimi-k2-*` (discontinuada Mayo 2026)
- `kimi-thinking-preview` (discontinuada Nov 2025)
- `kimi-latest` (discontinuada Ene 2026)

## Quality Criteria
- Kimi recibe la imagen correctamente (base64, mime type valido)
- No se envian parametros fijos (temperature, top_p, etc.)
- Timeout configurado a 120s (suficiente para imagenes)
- Errores HTTP se capturan y se propagan como `error_message`
- El error aparece en el dashboard (seccion de errores, polling 10s)
- Si Kimi falla, el sistema reporta el error y no bloquea la cola FIFO

## Edge Cases
- **API Key sin saldo:** Kimi responde 401/403. El error se muestra en dashboard.
- **Imagen > 100MB:** Rechazada por Kimi. Nuestro monitor ya limita a 15MB.
- **Timeout de 120s:** Se captura como `httpx.TimeoutException`.
- **Respuesta no-JSON:** Se maneja en el parser generico de `_parse_json_response`.
- **Rate limit (429):** Kimi tiene limites por plan. Esperar y reintentar manualmente.

## References
- Kimi API Docs: https://platform.kimi.ai/docs/overview
- Model List: https://platform.kimi.ai/docs/models
- Vision Models: https://platform.kimi.ai/docs/guide/use-kimi-vision-model
- Model Parameters: https://platform.kimi.ai/docs/api/models-overview
- Pricing: https://platform.kimi.ai/docs/pricing/chat-k26
- Billing Console: https://platform.kimi.ai/console/billing
- Related skills: `skill-image-extraction`, `skill-fifo-queue`
