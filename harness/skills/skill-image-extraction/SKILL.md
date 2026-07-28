# Skill: skill-image-extraction

## Identity
Eres un ingeniero de ML/inferencia especializado en modelos multimodales locales. Implementas la integracion con Ollama y Qwen3-VL para extraer datos estructurados de imagenes de tickets. Eres riguroso con la validacion del JSON de respuesta, la normalizacion de datos y el manejo de errores del modelo.

## Context
Esta skill implementa la extraccion de datos desde imagenes usando Ollama con Qwen3-VL (modelo seleccionado en Fase 0: 2B o 4B). Es el corazon de la automatizacion: sin esto, no hay datos que revisar ni enviar a Sheets.

Requisitos del PRD §7, §7.2, §16:
- Prompt estructurado que pide JSON con 5 campos + confianza
- Campos a extraer: transaction_date, amount, ticket_description, bank, transaction_type
- Validacion de JSON (estructura, tipos, campos requeridos)
- Normalizacion: fechas ISO 8601, montos float, tipos validos (Transferencia/Credito)
- Confianza por campo (0.0-1.0)
- Manejo de JSON malformado, campos faltantes, valores nulos
- Merge con EXIF si disponible

## Preconditions
- `skill-fifo-queue` completado (worker reclama trabajos y los envia aqui)
- `skill-database` completado (tablas `extraction_runs`, `expense_records`)
- Ollama corriendo con modelo Qwen3-VL (2B o 4B) cargado
- Directorio `prompts/` con archivo `expense_extraction.md` (o prompt inline)
- `uv` con dependencias: `requests` o `httpx` (para llamadas a Ollama)
- Rama `arnes` activa

## Execution

### Step 1: Crear el prompt de extraccion
1. Crear `prompts/expense_extraction.md` con el prompt estructurado exacto a enviar al modelo:
   ```
   Analiza esta imagen de un ticket/comprobante bancario...

   Reglas:
   - transaction_date en formato YYYY-MM-DD
   - amount como numero sin simbolo de moneda
   - bank: nombre del banco o "DESCONOCIDO"
   - transaction_type SOLO "Transferencia" o "Credito"
   - confidence entre 0.0 y 1.0
   - Responde UNICAMENTE con JSON, sin markdown, sin explicaciones
   ```
2. El prompt debe estar en espanol (los tickets estan en espanol)

### Step 2: Crear modulo de extraccion
1. Crear `app/extraction/__init__.py`
2. Crear `app/extraction/client.py`:

**Clase `OllamaClient`:**
```python
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = None, timeout: int = 300):
        self.base_url = base_url
        self.model = model or os.environ.get("GASTOSIA_OLLAMA_MODEL", "qwen3-vl:4b")
        self.timeout = timeout
        self.prompt = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Carga el prompt desde prompts/expense_extraction.md"""
    
    async def extract_from_image(self, image_path: str) -> ExtractionResult:
        """
        Envia imagen a Ollama y retorna resultado estructurado.
        
        Returns:
            ExtractionResult con datos extraidos, raw response, metadata
        
        Raises:
            OllamaTimeoutError: si tarda > timeout
            OllamaConnectionError: si no puede conectar
            InvalidJsonError: si la respuesta no es JSON valido
            MissingFieldsError: si faltan campos requeridos
        """
```

### Step 3: Implementar llamada a Ollama
En `app/extraction/client.py`:

```python
async def _call_ollama(self, image_path: str) -> dict:
    """Llama a Ollama API con la imagen en base64."""
    import base64
    
    with open(image_path, 'rb') as f:
        image_b64 = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "model": self.model,
        "prompt": self.prompt,
        "images": [image_b64],
        "stream": False,
        "options": {
            "temperature": 0.1,   # Baja temperatura para respuestas deterministicas
            "num_predict": 512,   # Limitar tokens de respuesta
        }
    }
    
    # Usar httpx para async
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()
```

### Step 4: Parsear y validar respuesta JSON
Crear `app/extraction/parser.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import json
import re

@dataclass
class ExtractionResult:
    transaction_date: Optional[date]
    amount: Optional[Decimal]
    ticket_description: Optional[str]
    bank: Optional[str]
    transaction_type: Optional[str]  # 'Transferencia' | 'Credito' | None
    confidence: dict[str, float]
    raw_response: str
    is_valid_json: bool
    parse_error: Optional[str]
    elapsed_ms: int
    model_name: str

def parse_ollama_response(raw_response: str) -> ExtractionResult:
    """
    Parsea la respuesta de Ollama y extrae los campos requeridos.
    
    Maneja:
    - JSON limpio
    - JSON dentro de bloques markdown (```json ... ```)
    - JSON con comillas escapadas
    - Campos faltantes (null)
    - Tipos incorrectos (convierte o asigna null)
    """
    
def validate_extraction(result: ExtractionResult) -> list[str]:
    """
    Valida los datos extraidos y retorna lista de warnings.
    
    Reglas:
    - transaction_date debe ser fecha valida
    - amount debe ser numero positivo
    - transaction_type debe ser 'Transferencia' o 'Credito'
    - bank no debe ser vacio
    """

def normalize_extraction(result: ExtractionResult) -> ExtractionResult:
    """
    Normaliza los datos extraidos:
    - Fecha: YYYY-MM-DD string -> date object
    - Monto: string/float -> Decimal con 2 decimales
    - Banco: uppercase, trim
    - Tipo: capitalize, validar contra lista permitida
    - Descripcion: strip, truncar a 500 chars
    """
```

### Step 5: Calcular confianza
En `app/extraction/confidence.py`:

```python
def evaluate_confidence(result: ExtractionResult) -> dict:
    """
    Evalua la confianza de la extraccion.
    
    PRD §16:
    - Alta: >= 0.90 -> visualizacion normal
    - Media: 0.70-0.89 -> advertencia
    - Baja: < 0.70 -> resaltado y revision
    
    Usa:
    1. Confianza reportada por el modelo (si existe en la respuesta)
    2. Heuristicas propias:
       - Fecha en el futuro -> baja confianza
       - Monto = 0 -> baja confianza
       - Banco = "DESCONOCIDO" -> baja confianza
       - Descripcion muy corta (< 3 chars) -> baja confianza
    3. Confianza agregada: promedio de confianzas por campo
    """
    
    confidence = result.confidence.copy()
    
    # Heuristicas adicionales
    if result.transaction_date and result.transaction_date > date.today():
        confidence['transaction_date'] = min(confidence.get('transaction_date', 0.5), 0.3)
    
    if result.amount and result.amount == 0:
        confidence['amount'] = min(confidence.get('amount', 0.5), 0.1)
    
    if result.bank and result.bank.upper() == 'DESCONOCIDO':
        confidence['bank'] = 0.1
    
    overall = sum(confidence.values()) / len(confidence) if confidence else 0.0
    
    return {
        **confidence,
        'overall': round(overall, 2)
    }
```

### Step 6: Integrar con el worker FIFO
En `app/queue/worker.py`, metodo `process_job()`:

```python
async def process_job(self, job: processing_queue):
    # 1. Obtener record_id y image_path
    # 2. Llamar a OllamaClient.extract_from_image()
    # 3. Parsear respuesta con parse_ollama_response()
    # 4. Validar con validate_extraction()
    # 5. Normalizar con normalize_extraction()
    # 6. Calcular confianza con evaluate_confidence()
    # 7. Guardar en expense_records:
    #    - transaction_date, amount, ticket_description, bank, transaction_type
    #    - confidence_json = json.dumps(confidence)
    # 8. Guardar en extraction_runs:
    #    - record_id, model_name, prompt_version, raw_response, parsed_json,
    #      is_valid_json, elapsed_ms
    # 9. Determinar estado final:
    #    - confidence['overall'] >= 0.70 -> LISTO_PARA_REVISION
    #    - confidence['overall'] < 0.70 -> REQUIERE_REVISION
    #    - Si parseo fallo -> ERROR_PROCESAMIENTO
```

### Step 7: Manejo de errores especificos
```python
# Errores que DEBEN manejarse:

# 1. Ollama no responde (connection refused)
try:
    response = await client.post(...)
except httpx.ConnectError:
    raise OllamaConnectionError("Ollama no esta corriendo en " + base_url)

# 2. Timeout (> 300 segundos)
except httpx.TimeoutException:
    raise OllamaTimeoutError(f"Timeout tras {timeout}s")

# 3. JSON invalido en respuesta
try:
    data = json.loads(clean_response)
except json.JSONDecodeError as e:
    # Intentar extraer JSON con regex
    match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            raise InvalidJsonError(f"JSON invalido: {e}")
    else:
        raise InvalidJsonError(f"No se encontro JSON en la respuesta")

# 4. Campos faltantes
required = ['transaction_date', 'amount', 'ticket_description', 'bank', 'transaction_type']
missing = [f for f in required if f not in data]
if missing:
    # No es fatal; los campos faltantes se dejan como null
    logger.warning(f"Campos faltantes en extraccion: {missing}")

# 5. Modelo no cargado en Ollama
if "model not found" in error_msg.lower():
    # Intentar cargar el modelo
    await client.post(f"{base_url}/api/pull", json={"name": model})
```

### Step 8: Generar evidencia
1. Crear `scripts/validation/test_image_extraction.py` que:
   - Pruebe extraccion con imagen de prueba de `ejemplos/`
   - Verifique que los 5 campos se extraen
   - Verifique formato de fecha (YYYY-MM-DD)
   - Verifique formato de monto (numero, 2 decimales)
   - Verifique transaction_type en {Transferencia, Credito}
   - Pruebe con imagen corrupta -> error manejado
   - Pruebe con imagen no relacionada (no es ticket) -> confianza baja
   - Verifique tiempo de respuesta < 300s
   - Verifique % de JSON valido en lote de 10 imagenes >= 99%
2. Ejecutar y generar evidencia

## Artifacts
- `prompts/expense_extraction.md`
- `app/extraction/__init__.py`
- `app/extraction/client.py`
- `app/extraction/parser.py`
- `app/extraction/confidence.py`
- `scripts/validation/test_image_extraction.py`
- `harness/evidence/fase1/extraccion-imagenes.json`
- `harness/evidence/fase1/extraccion-imagenes.md`

## Quality Criteria
- El prompt es claro, en espanol, y especifica formato JSON exacto
- La respuesta de Ollama se parsea correctamente en >= 99% de casos
- Campos faltantes no rompen el flujo (se asignan null + confianza 0.0)
- Fechas se normalizan a `date` objects (YYYY-MM-DD)
- Montos se normalizan a `Decimal` con 2 decimales
- Tipos de transaccion invalidos se convierten a None (no se inventan valores)
- Confianza se calcula combinando respuesta del modelo + heuristicas
- Timeout de Ollama configurable (default 300s)
- Errores de conexion se propagan claramente al worker
- Pruebas con al menos 10 imagenes del directorio `ejemplos/`

## Edge Cases
- **Ollama timeout a 300s:** worker captura, marca ERROR_PROCESAMIENTO
- **Modelo no cargado:** intentar `ollama pull` automaticamente; si falla, ERROR_PROCESAMIENTO
- **Respuesta JSON anidada en markdown:** limpiar ```json ... ``` antes de parsear
- **Imagen muy oscura/borrosa:** el modelo puede devolver campos null; marcar REQUIERE_REVISION
- **Imagen no es un ticket (ej. selfie):** confianza global baja, marcar REQUIERE_REVISION
- **Amount negativo (reembolso):** aceptar, es valido
- **Fecha en futuro:** marcar advertencia en confianza
- **Texto con caracteres especiales:** manejar UTF-8, truncar a 500 chars
- **Ollama se queda sin RAM:** el worker debe detectar y reintentar; si es recurrente, alertar
- **Campo 'bank' vacio o null:** asignar "DESCONOCIDO"

## References
- PRD §7 (Modelo multimodal)
- PRD §7.2 (Salida esperada - formato JSON)
- PRD §16 (Confianza - niveles y comportamiento)
- PRD §9.1 (Ingreso y analisis - flujo completo)
- Related skills: `skill-fifo-queue`, `skill-fase0-tecnica`
