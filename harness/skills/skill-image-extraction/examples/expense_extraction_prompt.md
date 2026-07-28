# Prompt de Extraccion de Gastos — Gastos IA
# Version: 1.0
# Modelo: Qwen3-VL (2B o 4B)

Analiza esta imagen de un ticket, comprobante bancario o captura de pantalla de transferencia y extrae los siguientes campos en formato JSON.

Responde UNICAMENTE con el JSON. No incluyas markdown, explicaciones, ni texto adicional.

{
  "transaction_date": "YYYY-MM-DD",
  "amount": 0.00,
  "ticket_description": "descripcion breve del gasto o concepto",
  "bank": "nombre del banco",
  "transaction_type": "Transferencia o Credito",
  "confidence": {
    "transaction_date": 0.0,
    "amount": 0.0,
    "ticket_description": 0.0,
    "bank": 0.0,
    "transaction_type": 0.0
  }
}

## Reglas para cada campo

### transaction_date
- Formato: YYYY-MM-DD (ejemplo: 2026-06-03)
- Busca la fecha de la transaccion, no la fecha del ticket si es diferente
- Si ves "HOY" o "AHORA", usa la fecha actual (no la pongas en el JSON, el sistema la asignara)
- Si no puedes determinar la fecha, usa null

### amount
- Solo el numero, sin simbolo de moneda ($, MXN, USD)
- Usa punto decimal (ejemplo: 700.00, no 700,00)
- Si es un cargo/retiro: numero negativo (ejemplo: -500.00)
- Si es un deposito/transferencia recibida: numero positivo
- Si no puedes leer el monto, usa null

### ticket_description
- Descripcion breve del establecimiento, concepto o referencia
- Ejemplos: "GASOL PUNTA SAM", "freelance Sarai", "Superama compra mensual"
- Maximo 100 caracteres
- Si no hay descripcion, usa null

### bank
- Nombre del banco: NU, Santander, BBVA, Banorte, HSBC, Citibanamex, etc.
- Si es transferencia entre cuentas, identifica el banco de origen
- Si no puedes identificarlo, usa "DESCONOCIDO"

### transaction_type
- SOLO uno de estos dos valores: "Transferencia" o "Credito"
- Transferencia: SPEI, transferencia bancaria, envio de dinero
- Credito: pago con tarjeta de credito, TPV, terminal punto de venta
- Si no puedes determinarlo, usa null

### confidence
- Numero entre 0.0 y 1.0 para cada campo
- 1.0 = totalmente seguro, el valor es claramente visible
- 0.5 = hay ambiguedad pero es la mejor estimacion
- 0.0 = no se pudo determinar, el campo debe ser null

## Ejemplos de tickets

### Ejemplo 1: Transferencia NU
Entrada: [Imagen de transferencia en app NU]
Salida:
{
  "transaction_date": "2026-06-03",
  "amount": 700.00,
  "ticket_description": "freelance Sarai PSAV 260524",
  "bank": "NU",
  "transaction_type": "Transferencia",
  "confidence": {
    "transaction_date": 0.97,
    "amount": 0.99,
    "ticket_description": 0.84,
    "bank": 0.96,
    "transaction_type": 0.94
  }
}

### Ejemplo 2: Ticket de gasolina
Entrada: [Imagen de ticket de gasolinera]
Salida:
{
  "transaction_date": "2026-07-23",
  "amount": 850.50,
  "ticket_description": "GASOL PUNTA SAM",
  "bank": "DESCONOCIDO",
  "transaction_type": "Credito",
  "confidence": {
    "transaction_date": 0.95,
    "amount": 0.98,
    "ticket_description": 0.90,
    "bank": 0.10,
    "transaction_type": 0.70
  }
}

## IMPORTANTE
- NO incluyas bloques de codigo markdown (```json)
- NO incluyas texto antes o despues del JSON
- SOLO el objeto JSON, nada mas
- Si la imagen no es un ticket/comprobante, devuelve todos los campos como null con confidence 0.0
