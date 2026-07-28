# PRD — Gastos IA

**Versión:** 1.2  
**Fecha:** 2026-07-28  
**Estado:** Aprobado para iniciar Fase 0  
**Tipo de solución:** Aplicación web local para extracción, revisión y registro de gastos  

---

## 1. Resumen ejecutivo

Gastos IA será una aplicación web alojada en una máquina virtual Ubuntu Server sobre Hyper-V. Detectará imágenes de tickets y comprobantes copiadas en carpetas compartidas del Windows Server, extraerá datos mediante un modelo multimodal local, permitirá revisarlos y enviará manualmente los registros aprobados a Google Sheets.

La solución operará principalmente dentro de la red local, sin utilizar servicios externos de inteligencia artificial ni APIs de IA con costo. PostgreSQL será la fuente principal de persistencia y auditoría. Google Sheets será el destino de negocio.

Los usuarios iniciales serán:

| Usuario | Rol |
|---|---|
| Ruben | Administrador |
| Esme | Estándar |

Todas las contraseñas, claves y secretos de ejecución se proporcionarán mediante variables de entorno. Ningún valor real podrá almacenarse en el código fuente, archivos versionados, imágenes, logs o historial de Git.

---

## 2. Objetivo

Automatizar la captura de gastos a partir de imágenes, reduciendo la transcripción manual y conservando revisión humana antes de modificar Google Sheets.

La aplicación deberá:

1. Detectar imágenes nuevas.
2. Evitar archivos incompletos y duplicados.
3. Extraer fecha, monto, descripción, banco y tipo de transacción.
4. Permitir correcciones desde el navegador.
5. Administrar categorías y cuentas.
6. Formar una descripción con grupo y consecutivo.
7. Insertar o actualizar el registro correcto en Google Sheets.
8. Conservar trazabilidad en PostgreSQL y logs JSONL.
9. Funcionar parcialmente sin Internet.
10. Iniciar automáticamente con el servidor.

---

## 3. Alcance del MVP

### 3.1 Incluido

- Windows Server como host.
- Hyper-V.
- Máquina virtual Ubuntu Server LTS.
- Aplicación web FastAPI.
- Interfaz HTML/Jinja/HTMX.
- PostgreSQL existente en el mismo servidor.
- Ollama y modelo multimodal local.
- Cola de procesamiento secuencial estricta FIFO para Ollama.
- Carpetas SMB para Ruben y Esme.
- Detección automática por sondeo.
- Revisión y corrección humana.
- Integración con Google Sheets.
- Catálogos de categorías y cuentas.
- Control de consecutivos.
- Prevención de duplicados.
- Historial y actualización de registros.
- HTTPS local con Caddy.
- Logs técnicos y auditoría.
- Instalador automatizado.
- Gestión de dependencias Python con `uv`.
- Integración con Git bajo aprobación humana.
- Secretos administrados mediante variables de entorno.

### 3.2 Fuera del alcance

- Aplicación móvil.
- Ejecución automática de pagos.
- Envío de imágenes a servicios externos de IA.
- OCR dedicado como Tesseract o servicios cloud.
- Acceso público desde Internet.
- Más de dos usuarios en el MVP.
- Respaldo automático.
- Modificación de la exposición actual de PostgreSQL.
- Commits, pushes o fusiones sin autorización explícita.

---

## 4. Usuarios y permisos

### 4.1 Ruben — administrador

Podrá:

- Ver todos los comprobantes.
- Revisar y editar todos los registros.
- Administrar categorías y cuentas.
- Administrar usuarios.
- Consultar logs funcionales.
- Reintentar procesos fallidos.

### 4.2 Esme — usuario estándar

Podrá:

- Ver sus comprobantes.
- Revisar y corregir sus registros.
- Enviar sus gastos.
- Consultar y actualizar su historial.

No podrá administrar catálogos ni usuarios.

---

## 5. Arquitectura

```text
Equipos de usuario
        │
        ├── SMB ──> Carpetas en Windows Server
        │
        └── HTTPS ─> Caddy
                       │
                       ▼
                    FastAPI
                 ┌─────┼───────────┐
                 ▼     ▼           ▼
            PostgreSQL Ollama   Google Sheets API
                         │
                         ▼
                      Qwen3-VL
```

### 5.1 Componentes

| Componente | Función |
|---|---|
| Windows Server | Host, carpetas SMB y PostgreSQL |
| Hyper-V | Alojar la VM |
| Ubuntu Server | Ejecutar la aplicación |
| FastAPI | Backend HTTP y API interna |
| HTML/Jinja/HTMX | Interfaz web |
| PostgreSQL | Persistencia principal |
| Ollama | Ejecución del modelo |
| Qwen3-VL | Análisis de imágenes |
| Trabajador FIFO | Procesar una sola imagen a la vez mediante Ollama |
| Caddy | HTTPS y proxy inverso |
| Google Sheets API | Lectura y escritura |
| SMB/CIFS | Acceso de la VM a imágenes |
| JSON Lines | Logs técnicos y auditoría |
| Git | Control de versiones |
| `uv` | Entorno y dependencias Python |

---

## 6. Infraestructura

### 6.1 Máquina virtual

| Recurso | Configuración inicial |
|---|---|
| RAM | 16 GB fijos |
| CPU | 4 vCPU, sujeto a validación |
| Disco | VHDX dinámico de 120 GB |
| Ubicación | `D:\Hyper-V\VirtualMachines\GastosIA` |
| Sistema | Ubuntu Server LTS |
| Red | Conmutador externo asociado a Ethernet |
| Inicio | Automático con el host |

### 6.2 Red

La evidencia inicial mostró:

- Wi-Fi: `192.168.100.171`.
- Ethernet: dirección APIPA `169.254.x.x`, sin configuración válida de red.

La configuración definitiva se realizará cuando el servidor esté conectado por Ethernet. Si la red cableada utiliza el mismo segmento, la dirección preferida será:

```text
192.168.100.75
```

Antes de asignarla, el instalador deberá validar subred, máscara, gateway, DNS, respuesta a ping y tabla ARP. Como no existe acceso al servidor DHCP, Ubuntu usará una IP estática validada.

### 6.3 HTTPS local

La aplicación se publicará como:

```text
https://gastos.local
```

Caddy generará un certificado interno. Se entregará un script para confiar en el certificado desde los dos equipos autorizados.

---

## 7. Modelo multimodal

La Fase 0 comparará:

```text
qwen3-vl:2b
qwen3-vl:4b
```

La variante 4B será la primera candidata por calidad; 2B será el fallback si el rendimiento en CPU resulta insuficiente. La GPU de 2 GB no formará parte del diseño inicial.

### 7.1 Criterios de comparación

- Exactitud de montos.
- Exactitud de fechas.
- Identificación de bancos.
- Clasificación de transacción.
- Descripción del gasto.
- JSON válido.
- Tiempo de procesamiento.
- Consumo de RAM.

### 7.2 Salida esperada

```json
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
```

Valores permitidos para `transaction_type`:

```text
Transferencia
Crédito
```

No se integrará un motor OCR separado. El modelo recibirá la imagen completa y devolverá datos estructurados.

---

## 8. Carpetas

### 8.1 Estructura

```text
D:\GastosIA\
├── Ruben\
│   ├── pendientes\
│   ├── procesados\YYYY\MM\
│   └── errores\
│       ├── duplicados\
│       └── procesamiento\
├── Esme\
│   ├── pendientes\
│   ├── procesados\YYYY\MM\
│   └── errores\
│       ├── duplicados\
│       └── procesamiento\
└── logs\
```

Rutas compartidas:

```text
\\SERVIDOR\GastosIA\Ruben\pendientes
\\SERVIDOR\GastosIA\Esme\pendientes
```

Por decisión del proyecto no se aplicarán restricciones adicionales por usuario a estas carpetas.

### 8.2 Monitoreo

La VM montará el recurso SMB mediante CIFS. La aplicación usará sondeo cada cinco segundos.

Antes de procesar una imagen deberá comprobar:

1. Tamaño estable durante tres verificaciones.
2. Fecha de modificación estable.
3. Apertura completa del archivo.
4. Extensión compatible.

Durante las validaciones de existencia, metadatos, estabilidad y apertura, el monitor deberá capturar explícitamente bloqueos temporales de SMB o del sistema operativo. Esto incluye, como mínimo:

- `PermissionError`.
- `OSError` asociado con acceso denegado, recurso ocupado o violación de uso compartido.
- Códigos equivalentes a `EACCES`, `EBUSY` o bloqueo temporal.

Un bloqueo temporal no deberá cambiar el registro a `ERROR_PROCESAMIENTO`, mover el archivo ni generar una alerta al usuario. La aplicación lo ignorará silenciosamente, mantendrá el archivo en `ESPERANDO_ARCHIVO_ESTABLE`, reiniciará el contador de estabilidad y volverá a intentarlo en el siguiente ciclo de cinco segundos.

---

## 9. Flujo funcional

### 9.1 Ingreso y análisis

1. El usuario copia una imagen a `pendientes`.
2. El monitor detecta y valida el archivo.
3. Se calcula SHA-256.
4. Se bloquean duplicados exactos.
5. Se corrige orientación EXIF.
6. Se crea una copia optimizada para inferencia.
7. Se conserva el original.
8. El registro se agrega a la cola con estado `EN_COLA`.
9. El trabajador FIFO toma el primer registro elegible.
10. El registro cambia a `ANALIZANDO`.
11. Se envía una única imagen a Ollama.
12. El modelo devuelve JSON.
13. Se validan y normalizan los datos.
14. El registro cambia a `LISTO_PARA_REVISION` o `REQUIERE_REVISION`.

### 9.2 Cola de procesamiento secuencial estricta

La integración con Ollama deberá implementar una cola persistente, secuencial y estrictamente FIFO:

1. Solo podrá existir una solicitud de análisis activa contra Ollama.
2. El trabajador de inferencia tendrá concurrencia efectiva igual a `1`.
3. Las imágenes se ordenarán por `enqueued_at` ascendente y, para desempates, por `record_id` ascendente.
4. La imagen que espera turno permanecerá en `EN_COLA`; únicamente la imagen entregada a Ollama podrá estar en `ANALIZANDO`.
5. La siguiente imagen no podrá enviarse a Ollama hasta que el proceso anterior haya finalizado, ya sea con éxito o con `ERROR_PROCESAMIENTO`.
6. La cola y sus transiciones se persistirán en PostgreSQL para sobrevivir reinicios del servicio o del servidor.
7. La toma de un trabajo deberá ser atómica y protegida con bloqueo de base de datos, de forma que dos procesos no puedan reclamar la misma imagen.
8. El sistema deberá impedir que una configuración accidental con varios procesos web produzca más de un trabajador de inferencia activo.
9. Al reiniciar, un trabajo que haya quedado en `ANALIZANDO` sin ejecución activa deberá recuperarse de forma controlada y volver a `EN_COLA`, sin duplicar registros.
10. No se permitirá enviar imágenes directamente a Ollama omitiendo esta cola.

### 9.3 Revisión

El usuario:

1. Abre el comprobante.
2. Compara imagen y extracción.
3. Corrige los campos permitidos.
4. Selecciona categoría y cuenta.
5. Captura el grupo.
6. Revisa la descripción final.
7. Presiona **Enviar a Google Sheets**.

### 9.4 Envío

Antes de enviar:

1. Se verifica Internet.
2. Se sincronizan catálogos.
3. Se consulta `_Control`.
4. Se revalidan duplicados.
5. Se recalcula el consecutivo.
6. Se determina la pestaña mensual.
7. Se crea si no existe.
8. Se inserta el registro.
9. Se actualiza `_Control`.
10. Se mueve la imagen a `procesados/YYYY/MM`.
11. Se registra auditoría.

### 9.5 Operación sin Internet

Sin Internet será posible detectar, analizar, revisar, corregir y guardar localmente. El estado será `PENDIENTE_DE_ENVIO`. El envío se habilitará nuevamente cuando Google Sheets esté disponible y deberá ser iniciado manualmente.

---

## 10. Interfaz web

### 10.1 Autenticación

- Usuario y contraseña.
- Hash Argon2id.
- Sesiones con caducidad.
- Cookies `HttpOnly`, `Secure` y `SameSite`.
- Bloqueo temporal por intentos fallidos.
- Cambio obligatorio de contraseña inicial.

Las contraseñas reales de los usuarios no se conservarán como variables permanentes. Las variables de contraseña inicial solo existirán durante el alta; la aplicación almacenará únicamente el hash Argon2id.

### 10.2 Pantalla principal

| Campo | Descripción |
|---|---|
| Miniatura | Vista reducida |
| Archivo | Nombre original |
| Fecha | Fecha extraída |
| Monto | Importe detectado |
| Banco | Banco detectado |
| Estado | Estado actual |
| Advertencias | Campos de baja confianza |
| Propietario | Visible para Ruben |

#### 10.2.1 Actualización automática de estados

La interfaz deberá usar **HTMX Polling cada tres segundos** para reflejar los cambios de estado sin recargar la página completa.

- Cada fila o bloque de comprobante consultará un endpoint HTML parcial, por ejemplo `GET /expenses/{record_id}/status`.
- El servidor responderá con un fragmento Jinja que contenga el estado, las advertencias y las acciones disponibles.
- HTMX reemplazará únicamente el fragmento correspondiente.
- La vista deberá reflejar transiciones como `EN_COLA` → `ANALIZANDO` → `LISTO_PARA_REVISION` o `REQUIERE_REVISION`.
- El sondeo podrá detenerse cuando el comprobante alcance un estado que ya no cambie por procesamiento en segundo plano y reanudarse cuando exista una nueva operación asíncrona.
- Ruben y Esme deberán ver los cambios conforme a sus permisos, sin presionar `F5`.

WebSockets no formarán parte del MVP. SSE solo podrá evaluarse posteriormente si el sondeo demuestra una carga injustificada; no será necesario para aprobar esta versión.

### 10.3 Revisión individual

La imagen permitirá ampliar, reducir, rotar, ajustar al ancho y abrir en tamaño completo. El formulario aparecerá al lado de la imagen.

### 10.4 Historial

Permitirá filtrar por usuario, fecha, banco y grupo; consultar pestaña y fila; editar registros autorizados y actualizar Google Sheets.

### 10.5 Catálogos

Solo Ruben podrá crear, editar, activar y desactivar categorías, cuentas y usuarios. Los valores ya utilizados no se eliminarán físicamente.

---

## 11. Campos visibles y reglas

| Campo | Control | Fuente o valor | Editable |
|---|---|---|---|
| Fecha del gasto | Calendario | Detectada en la imagen | Sí |
| Grupo | Texto | Captura del usuario | Sí |
| Descripción del ticket | Texto | Motivo o concepto detectado | Sí |
| Descripción final | Vista previa | Grupo + consecutivo + descripción | No |
| Categoría | Dropdown | Catálogo administrable | Selección |
| Empleado | Oculto o lectura | `RUBEN BENJAMIN VAZQUEZ EMBRIZ` | No |
| Pagado por | Oculto o lectura | `Empresa` | No |
| Actividades | Oculto | Vacío | No |
| Fecha contable | Oculto | Vacío | No |
| Cuenta | Dropdown | Catálogo administrable | Selección |
| Precio unitario | Numérico | Monto detectado | Sí |
| Cantidad | Oculto o lectura | `1` | No |
| Incluir impuestos | Oculto | Vacío | No |
| Importe de impuestos | Oculto | Vacío | No |
| Total | Numérico | Monto detectado | Sí |
| Estado | Oculto o lectura | `Por reportar` | No |
| Banco | Texto | Banco detectado | Sí |
| Tipo de transacción | Dropdown | Transferencia o Crédito | Sí |

Como la cantidad será siempre `1`:

```text
Precio unitario = Total
```

Modificar uno actualizará el otro.

### 11.1 Campos obligatorios

El botón de envío permanecerá deshabilitado mientras falte fecha, grupo, descripción, categoría, cuenta, precio unitario, total, banco o tipo de transacción.

---

## 12. Descripción y consecutivo

Formato:

```text
GRUPO-Consecutivo-Descripción del ticket
```

Ejemplo:

```text
VAL-260723-3-GASOL PUNTA SAM
```

La aplicación normalizará espacios, mayúsculas y caracteres permitidos. El siguiente consecutivo será el máximo existente más uno, considerando registros locales, `_Control` e históricos importados.

PostgreSQL aplicará un bloqueo lógico temporal por grupo. Antes de escribir en Sheets se realizará una segunda validación.

---

## 13. Google Sheets

### 13.1 Columnas mensuales

| Posición | Columna |
|---:|---|
| 1 | Fecha del gasto |
| 2 | Categoría |
| 3 | Descripción |
| 4 | Empleado |
| 5 | Pagado por |
| 6 | Actividades |
| 7 | Fecha contable |
| 8 | Cuenta |
| 9 | Precio unitario |
| 10 | Cantidad |
| 11 | Incluir impuestos |
| 12 | Importe de impuestos |
| 13 | Total |
| 14 | Estado |
| 15 | Banco |
| 16 | Transaccion |

No se agregarán columnas técnicas a las pestañas mensuales.

### 13.2 Mapeo

| Columna | Fuente |
|---|---|
| Fecha del gasto | Fecha detectada o corregida |
| Categoría | Catálogo |
| Descripción | Descripción final |
| Empleado | `RUBEN BENJAMIN VAZQUEZ EMBRIZ` |
| Pagado por | `Empresa` |
| Actividades | Vacío |
| Fecha contable | Vacío |
| Cuenta | Catálogo |
| Precio unitario | Monto corregido |
| Cantidad | `1` |
| Incluir impuestos | Vacío |
| Importe de impuestos | Vacío |
| Total | Monto corregido |
| Estado | `Por reportar` |
| Banco | Banco corregido |
| Transaccion | `Transferencia` o `Crédito` |

### 13.3 Pestañas mensuales

El nombre dependerá de la fecha del gasto:

```text
Agosto-26
Septiembre-26
Enero-27
```

Si no existe, se creará desde cero con los 16 encabezados.

### 13.4 Pestañas técnicas ocultas

- `_Categorias`: código, descripción y activo.
- `_Cuentas`: código, descripción y activo.
- `_Control`: trazabilidad, duplicados, consecutivos y ubicación de filas.

Campos mínimos de `_Control`:

```text
record_id
image_hash
owner
group_code
consecutive
final_description
expense_date
amount
bank
transaction_type
sheet_name
sheet_row
status
source_filename
created_at
updated_at
```

---

## 14. Actualización de registros

### 14.1 Mismo mes

Se localizará y actualizará la fila, las 16 columnas, `_Control` y la auditoría.

### 14.2 Cambio de mes

Se insertará el registro en la pestaña nueva, se eliminará la fila anterior y se actualizarán `_Control` y auditoría.

### 14.3 Fila alterada manualmente

La aplicación intentará conciliarla usando la descripción final y `_Control`. Si hay varias coincidencias, bloqueará la actualización y no creará un duplicado.

---

## 15. Duplicados

### 15.1 Exacto

Criterio: SHA-256 de la imagen.

Acciones:

- Bloquear procesamiento.
- No crear un gasto.
- Mover a `errores/duplicados`.
- Mostrar el registro original.
- Registrar el evento.

### 15.2 Probable

Criterios: misma fecha, monto, banco y descripción igual o similar.

Se advertirá al propietario, quien podrá confirmar el envío. La decisión quedará auditada.

---

## 16. Confianza

| Nivel | Rango | Comportamiento |
|---|---:|---|
| Alta | `>= 0.90` | Visualización normal |
| Media | `0.70–0.89` | Advertencia |
| Baja | `< 0.70` | Resaltado y revisión |

La confianza no bloqueará por sí sola el registro.

---

## 17. Estados

```text
DETECTADO
ESPERANDO_ARCHIVO_ESTABLE
EN_COLA
ANALIZANDO
LISTO_PARA_REVISION
REQUIERE_REVISION
PENDIENTE_DE_ENVIO
ENVIANDO
ENVIADO
ACTUALIZANDO
ACTUALIZADO
DUPLICADO_EXACTO
DUPLICADO_PROBABLE
ERROR_PROCESAMIENTO
ERROR_SHEETS
```

Reglas obligatorias:

- Podrán existir varios registros en `EN_COLA`.
- Solo podrá existir un registro en `ANALIZANDO`.
- `EN_COLA` significa que el archivo está validado y espera su turno FIFO.
- `ANALIZANDO` significa que la imagen ya fue reclamada por el trabajador y está siendo procesada por Ollama.
- Las transiciones de estado deberán persistirse antes de actualizar la interfaz.

---

## 18. PostgreSQL

```text
Base de datos: gastos_ia
Usuario: gastos_app
```

El instalador no modificará `postgresql.conf`, `pg_hba.conf`, firewall ni la exposición actual de PostgreSQL.

Tablas mínimas:

```text
users
expense_records
image_files
extraction_runs
processing_queue
catalog_cache
sheet_sync
audit_events
system_settings
```

PostgreSQL almacenará usuarios, hashes de contraseña, hashes de imágenes, estados, datos detectados y corregidos, consecutivos, referencias de Sheets, auditoría y configuración no secreta.

---

## 19. Variables de entorno y secretos

### 19.1 Regla obligatoria

Toda contraseña, clave, token o secreto deberá entrar a la aplicación mediante variables de entorno. Se prohíbe incluir valores reales en:

- Código fuente.
- `pyproject.toml`.
- Archivos Markdown.
- Dockerfiles.
- `compose.yaml`.
- Scripts.
- Plantillas.
- Pruebas y fixtures.
- Logs.
- Imágenes.
- Commits o historial de Git.

### 19.2 Variables mínimas

| Variable | Propósito | Obligatoria | Persistencia |
|---|---|---:|---|
| `GASTOSIA_DATABASE_HOST` | Host PostgreSQL | Sí | Entorno del servicio |
| `GASTOSIA_DATABASE_PORT` | Puerto PostgreSQL | Sí | Entorno del servicio |
| `GASTOSIA_DATABASE_NAME` | Base `gastos_ia` | Sí | Entorno del servicio |
| `GASTOSIA_DATABASE_USER` | Usuario `gastos_app` | Sí | Entorno del servicio |
| `GASTOSIA_DATABASE_PASSWORD` | Contraseña de `gastos_app` | Sí | Entorno del servicio |
| `GASTOSIA_SESSION_SECRET` | Firma de sesiones | Sí | Entorno del servicio |
| `GASTOSIA_SMB_USERNAME` | Usuario del recurso SMB | Sí | Entorno del servicio |
| `GASTOSIA_SMB_PASSWORD` | Contraseña SMB | Sí | Entorno del servicio |
| `GASTOSIA_GOOGLE_CREDENTIALS_PATH` | Ruta al JSON fuera del repo | Sí | Entorno del servicio |
| `GASTOSIA_GOOGLE_SPREADSHEET_ID` | ID del archivo de Sheets | Sí | Entorno del servicio |
| `GASTOSIA_RUBEN_INITIAL_PASSWORD` | Alta inicial de Ruben | Solo instalación | Temporal |
| `GASTOSIA_ESME_INITIAL_PASSWORD` | Alta inicial de Esme | Solo instalación | Temporal |
| `GASTOSIA_POSTGRES_ADMIN_PASSWORD` | Crear base/usuario | Solo instalación | Temporal |

### 19.3 Contraseñas de Ruben y Esme

1. El instalador solicitará las contraseñas sin mostrarlas en pantalla.
2. Las inyectará temporalmente como variables de entorno del proceso de inicialización.
3. La aplicación generará hashes Argon2id.
4. PostgreSQL guardará únicamente los hashes.
5. Las variables `GASTOSIA_RUBEN_INITIAL_PASSWORD` y `GASTOSIA_ESME_INITIAL_PASSWORD` se eliminarán al terminar.
6. Los valores no aparecerán en argumentos de línea de comandos, reportes ni logs.
7. En el primer acceso se exigirá cambio de contraseña.

### 19.4 Servicios en Ubuntu

Las variables permanentes podrán cargarse desde un archivo de entorno fuera del repositorio:

```text
/etc/gastos-ia/gastos-ia.env
```

Requisitos:

- Propietario `root`.
- Permisos `0600`.
- No ubicado dentro del proyecto Git.
- No servido por FastAPI o Caddy.
- No incluido en diagnósticos.
- No copiado a respaldos por la aplicación.
- Inyectado al proceso mediante `systemd` o el mecanismo de despliegue aprobado.

El archivo deberá contener valores con formato `NOMBRE=valor`, sin usar `export`.

### 19.5 Plantilla versionable

El repositorio incluirá solo `.env.example`, sin valores reales:

```dotenv
GASTOSIA_APP_ENV=production
GASTOSIA_DATABASE_HOST=
GASTOSIA_DATABASE_PORT=5432
GASTOSIA_DATABASE_NAME=gastos_ia
GASTOSIA_DATABASE_USER=gastos_app
GASTOSIA_DATABASE_PASSWORD=
GASTOSIA_SESSION_SECRET=
GASTOSIA_SMB_USERNAME=
GASTOSIA_SMB_PASSWORD=
GASTOSIA_GOOGLE_CREDENTIALS_PATH=
GASTOSIA_GOOGLE_SPREADSHEET_ID=
GASTOSIA_RUBEN_INITIAL_PASSWORD=
GASTOSIA_ESME_INITIAL_PASSWORD=
GASTOSIA_POSTGRES_ADMIN_PASSWORD=
```

### 19.6 Validación

Al iniciar, la aplicación deberá:

1. Confirmar que todas las variables requeridas existen.
2. Rechazar secretos vacíos o de longitud insegura.
3. No imprimir valores en mensajes de error.
4. Enmascarar secretos en diagnósticos.
5. Fallar de forma segura si falta una variable.

---

## 20. Credencial de Google

El JSON de la cuenta de servicio no se guardará en Git. Permanecerá fuera del repositorio con permisos restrictivos.

La variable:

```text
GASTOSIA_GOOGLE_CREDENTIALS_PATH
```

contendrá únicamente su ruta. La cuenta de servicio tendrá acceso como editor solo al archivo requerido.

---

## 21. Logs JSONL

Archivos:

```text
app-YYYY-MM-DD.jsonl
audit-YYYY-MM-DD.jsonl
install-YYYY-MM-DD.jsonl
```

Los logs no contendrán contraseñas, variables sensibles, tokens, JSON de Google, números completos de tarjeta ni datos bancarios sensibles. Se conservarán indefinidamente y podrán comprimirse.

---

## 22. Seguridad

- Acceso solo desde red local.
- HTTPS obligatorio.
- Argon2id para contraseñas.
- Cookies seguras y sesiones con caducidad.
- Variables de entorno para secretos.
- Archivo de entorno fuera de Git y con permisos `0600`.
- Credencial de Google con mínimo privilegio.
- Usuario PostgreSQL limitado a `gastos_ia`.
- Ollama no expuesto directamente.
- Imágenes nunca enviadas a IA externa.
- Auditoría de accesos y modificaciones.
- Escaneo de secretos antes de cada commit.

---

## 23. Instalación automatizada

Archivo principal:

```text
install-gastos-ia.ps1
```

El instalador deberá:

1. Ejecutar prevalidaciones.
2. Validar virtualización.
3. Habilitar Hyper-V y gestionar reinicio.
4. Crear carpetas y recursos SMB.
5. Crear conmutador virtual.
6. Descargar e instalar Ubuntu.
7. Crear y configurar la VM.
8. Instalar Docker o servicios aprobados.
9. Instalar Ollama y modelos de prueba.
10. Desplegar FastAPI y Caddy.
11. Montar las carpetas SMB.
12. Crear base y usuario PostgreSQL.
13. Inicializar tablas.
14. Configurar credencial de Google.
15. Crear usuarios Ruben y Esme.
16. Configurar variables de entorno.
17. Configurar inicio automático.
18. Ejecutar pruebas.
19. Generar diagnóstico JSON sin secretos.

### 23.1 Datos humanos requeridos

- Contraseña inicial de Ruben.
- Contraseña inicial de Esme.
- Contraseña administrativa de PostgreSQL.
- Contraseña del usuario de aplicación PostgreSQL.
- Credenciales SMB.
- JSON de cuenta de servicio.
- ID de Google Sheets.
- Parámetros de red.
- Confirmación de IP estática.

Los campos de contraseña se solicitarán como entrada segura y se inyectarán en variables de entorno; no se escribirán en consola.

---

## 24. Inicio automático

Al arrancar el host:

1. Hyper-V iniciará la VM.
2. Ubuntu iniciará servicios.
3. Se cargarán las variables de entorno protegidas.
4. Se validará PostgreSQL.
5. Ollama cargará el modelo bajo demanda.
6. FastAPI y Caddy iniciarán.
7. El monitor revisará las carpetas.

Los servicios tendrán reinicio automático ante fallos.

---

## 25. Git

El usuario creará el repositorio. La solución no creará repositorios remotos ni configurará credenciales personales.

### 25.1 Reglas

1. No trabajar directamente sobre `main`.
2. Desarrollar cada componente en una rama.
3. Permitir cambios, pruebas, `git diff` y `git status`.
4. No ejecutar `git commit` sin validación funcional y autorización.
5. No ejecutar `git push` sin autorización explícita.
6. No fusionar ramas ni publicar versiones por iniciativa propia.
7. No mezclar componentes sin relación.
8. Ejecutar escaneo de secretos antes de cada commit.

### 25.2 Flujo

```text
Crear rama
    ↓
Desarrollar componente
    ↓
Ejecutar pruebas
    ↓
Mostrar diferencias y resultados
    ↓
Validación del usuario
    ↓
Autorización explícita
    ↓
Commit
    ↓
Autorización independiente para push
```

### 25.3 Ramas sugeridas

```text
feat/folder-monitor
feat/image-extraction
feat/authentication
feat/catalogs
feat/google-sheets
feat/expense-history
feat/installer
fix/<descripcion>
```

Antes de solicitar un commit se presentarán componente, archivos modificados, pruebas, errores conocidos, escaneo de secretos, resumen del diff y mensaje propuesto.

---

## 26. Protección del repositorio

No podrán versionarse:

- `.env` reales.
- Archivo JSON de cuenta de servicio.
- Contraseñas o tokens.
- Credenciales SMB.
- Certificados o llaves privadas.
- Imágenes reales de comprobantes.
- Logs.
- Exportaciones de Google Sheets.
- Backups de PostgreSQL.
- Modelos locales.

`.gitignore` mínimo:

```gitignore
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.venv/

.env
.env.*
!.env.example
credentials/
secrets/
*.pem
*.key
*.p12
*.pfx
*service-account*.json
*credentials*.json

data/
logs/
uploads/
pendientes/
procesados/
errores/
*.db
*.sqlite*
*.dump
*.backup

models/
*.gguf
*.safetensors

.vscode/
.idea/
.DS_Store
Thumbs.db
```

Si un secreto llega al historial, deberá revocarse y sustituirse; borrar el archivo no será suficiente.

---

## 27. Gestión Python con `uv`

`uv` será la herramienta exclusiva para entornos, dependencias, bloqueo, ejecución, pruebas y herramientas de calidad.

Archivos:

```text
pyproject.toml
uv.lock
.python-version
```

El `uv.lock` se versionará y solo se modificará mediante `uv`. `.venv/` nunca se versionará.

Se separarán dependencias de producción y desarrollo. Como mínimo se usarán:

- `pytest`.
- `ruff`.
- `mypy`.
- Cobertura.
- Escáner de dependencias.
- Escáner de secretos.

No se utilizarán `pip install` manual, Poetry, Pipenv o Conda para administrar el proyecto.

---

## 28. Puerta de calidad

Antes de cada commit:

```text
Dependencias sincronizadas
        ↓
Formato y lint
        ↓
Tipos
        ↓
Pruebas unitarias
        ↓
Pruebas de integración
        ↓
Seguridad de dependencias
        ↓
Escaneo de secretos
        ↓
Prueba funcional
        ↓
Autorización humana
```

Si una validación falla, no habrá commit.

---

## 29. Estructura del repositorio

```text
gastos-ia/
├── app/
│   ├── api/
│   ├── auth/
│   ├── catalogs/
│   ├── database/
│   ├── expenses/
│   ├── images/
│   ├── sheets/
│   ├── users/
│   └── main.py
├── migrations/
├── templates/
├── static/
├── prompts/
│   └── expense_extraction.md
├── scripts/
│   ├── install/
│   ├── diagnostics/
│   └── validation/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── deployment/
│   ├── systemd/
│   ├── caddy/
│   ├── hyperv/
│   └── ubuntu/
├── docs/
│   └── adr/
├── credentials/
│   └── README.md
├── .env.example
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 30. ADR

Se documentarán como mínimo:

```text
ADR-001-uso-de-ubuntu-en-hyper-v.md
ADR-002-modelo-multimodal-local.md
ADR-003-postgresql-existente.md
ADR-004-google-sheets-como-destino.md
ADR-005-uv-para-dependencias.md
ADR-006-politica-de-commits-validados.md
ADR-007-secretos-mediante-variables-de-entorno.md
```

---

## 31. Requisitos no funcionales

### 31.1 Rendimiento

| Métrica | Objetivo |
|---|---:|
| Detección de imagen | ≤ 15 segundos |
| Procesamiento por imagen | ≤ 5 minutos |
| Apertura de interfaz | ≤ 3 segundos |
| Envío a Sheets | ≤ 15 segundos |
| Usuarios simultáneos | 2 |
| Volumen | < 100 imágenes/día |

### 31.2 Confiabilidad

- Ningún reintento duplicará registros.
- Un fallo de Internet no perderá datos.
- La imagen solo se moverá después del envío confirmado.
- Todo cambio será auditable.
- Un reinicio conservará pendientes.
- La cola FIFO sobrevivirá reinicios y no permitirá más de una inferencia activa.
- Un bloqueo temporal de SMB no se tratará como error definitivo.
- Los navegadores reflejarán cambios de estado mediante HTMX Polling sin recarga completa.

### 31.3 Compatibilidad

```text
.jpg
.jpeg
.png
.webp
```

Tamaño máximo inicial: `15 MB`.

---

## 32. Métricas de calidad

La Fase 0 usará al menos 50 comprobantes reales anonimizados.

| Campo | Objetivo |
|---|---:|
| Monto exacto | ≥ 95% |
| Fecha exacta | ≥ 90% |
| Banco correcto | ≥ 90% |
| Tipo correcto | ≥ 90% |
| JSON válido | ≥ 99% |
| Duplicados exactos creados | 0 |
| Registros perdidos | 0 |

Si Qwen3-VL 4B no alcanza estos objetivos, se evaluará otro modelo visual local.

---

## 33. Criterios de aceptación

El MVP será aceptado cuando:

1. La VM y servicios inicien automáticamente.
2. La página sea accesible desde ambos equipos.
3. Ruben y Esme puedan iniciar sesión.
4. Los roles funcionen.
5. Las carpetas asignen correctamente propietario.
6. Se detecten imágenes estables.
7. Un archivo temporalmente bloqueado por SMB permanezca en espera y se reintente sin pasar a error.
8. Las imágenes validadas entren a una cola FIFO persistente.
9. Solo una imagen pueda estar en `ANALIZANDO` y solo una solicitud llegue a Ollama a la vez.
10. La segunda imagen permanezca en `EN_COLA` hasta que termine la primera.
11. El orden de procesamiento coincida con `enqueued_at` y `record_id`.
12. Un reinicio recupere la cola sin perder ni duplicar trabajos.
13. La interfaz muestre la imagen.
14. Los estados se actualicen mediante HTMX Polling cada tres segundos sin usar `F5`.
15. Ruben y Esme vean las transiciones permitidas por su rol.
16. El modelo extraiga los cinco campos requeridos.
17. La confianza genere advertencias.
18. La fecha sea corregible.
19. Precio unitario y total permanezcan sincronizados.
20. Categoría y cuenta sean dropdowns.
21. El consecutivo evite colisiones.
22. La descripción final se genere automáticamente.
23. El botón se bloquee si faltan campos.
24. Los duplicados exactos se bloqueen.
25. Los probables generen advertencia.
26. El registro llegue a la pestaña mensual correcta.
27. Se creen pestañas con 16 encabezados.
28. La imagen se mueva solo después del envío.
29. El historial permita consultar y actualizar.
30. El cambio de mes mueva el registro.
31. La operación sin Internet conserve el gasto.
32. Los logs JSONL se generen sin secretos.
33. El reinicio no pierda estados.
34. No se use una API de IA con costo.
35. El repositorio use `uv`.
36. Ningún secreto esté versionado.
37. Las contraseñas se entreguen mediante variables de entorno.
38. Solo los hashes Argon2id de usuarios persistan en PostgreSQL.
39. No haya commits ni pushes sin autorización.

---

## 34. Fases

### Fase 0 — Prueba técnica

- Validar Hyper-V y red.
- Probar Qwen3-VL 2B y 4B con 50 imágenes.
- Validar PostgreSQL.
- Validar cuenta de servicio y Google Sheets.
- Importar datos históricos a `_Control`.
- Validar el mecanismo de variables de entorno.

### Fase 1 — Núcleo

- Base de datos.
- Usuarios.
- Carpetas.
- Monitor.
- Manejo de bloqueos temporales SMB.
- Cola FIFO persistente con un único trabajador de Ollama.
- Extracción.
- Estados y logs.

### Fase 2 — Interfaz

- Login.
- Pendientes.
- Actualización automática mediante HTMX Polling.
- Visor.
- Formulario.
- Catálogos.
- Historial.

### Fase 3 — Google Sheets

- Sincronización.
- Pestañas mensuales y técnicas.
- Consecutivos.
- Actualizaciones.
- Movimiento entre meses.

### Fase 4 — Instalador

- PowerShell.
- Hyper-V.
- Ubuntu desatendido.
- Despliegue.
- Variables de entorno.
- Inicio automático.
- Diagnóstico JSON.

### Fase 5 — Aceptación

- Pruebas funcionales.
- Concurrencia.
- Orden FIFO y exclusión mutua de Ollama.
- Recuperación de cola después de reinicio.
- Bloqueos temporales de archivos SMB.
- Actualización de estados en dos navegadores.
- Operación sin Internet.
- Reinicios.
- Comprobantes reales.
- Manual operativo.

---

## 35. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Modelo no lee ciertos tickets | Alto | Benchmark y cambio de modelo |
| Inferencia lenta por CPU | Medio | Cola, modelo 2B u optimización |
| Más de un proceso llama a Ollama | Alto | Cola persistente, trabajador único y bloqueo en PostgreSQL |
| Trabajo queda tomado tras un reinicio | Alto | Recuperación controlada de `ANALIZANDO` a `EN_COLA` |
| Bloqueo temporal de archivo SMB | Medio | Capturar excepción y reintentar en el siguiente sondeo |
| Estado desactualizado en el navegador | Medio | HTMX Polling cada tres segundos |
| IP dentro del rango DHCP | Alto | Validación previa |
| Manipulación manual de Sheets | Medio | `_Control` y conciliación |
| Imagen en carpeta incorrecta | Medio | Mostrar propietario |
| Falla del disco `D:` | Alto | Riesgo aceptado; sin backups |
| Credencial de Google comprometida | Alto | Mínimo privilegio y rotación |
| Secreto expuesto en Git | Alto | `.gitignore`, escaneo, revocación |
| Variable visible en diagnóstico | Alto | Enmascarado y pruebas |
| Fin de soporte de Windows Server 2016 | Alto | Plan de actualización del host |

---

## 36. Restricción de respaldos

Por decisión del proyecto, la aplicación no realizará respaldos automáticos de imágenes, configuración, logs, PostgreSQL o la VM.

La retención indefinida no equivale a respaldo. Una falla del disco puede provocar pérdida total; el riesgo queda aceptado.

---

## 37. Resultado esperado

```text
Copiar imagen
      ↓
Detección automática
      ↓
Cola FIFO (`EN_COLA`)
      ↓
Análisis multimodal local
      ↓
Revisión en navegador
      ↓
Categoría + Cuenta + Grupo
      ↓
Consecutivo automático
      ↓
Envío manual
      ↓
Google Sheets
      ↓
Imagen a procesados
      ↓
Historial y auditoría
```

---

## 38. Decisiones aprobadas

- La solución se ejecutará en una VM Ubuntu sobre Hyper-V.
- La VM tendrá inicialmente 16 GB de RAM, 4 vCPU y VHDX dinámico de 120 GB.
- El disco se ubicará en `D:`.
- Se usará PostgreSQL existente.
- No se modificarán sus reglas de exposición.
- No habrá respaldos automáticos.
- Se usarán Ollama y un modelo multimodal local.
- Ollama procesará una sola imagen a la vez mediante una cola FIFO persistente.
- La interfaz actualizará estados con HTMX Polling cada tres segundos.
- Los bloqueos temporales de archivos SMB se reintentarán sin marcar error.
- Ruben será administrador y Esme usuario estándar.
- Google Sheets conservará exactamente 16 columnas de negocio.
- El usuario creará el repositorio Git.
- No habrá commits sin validación.
- No habrá pushes sin autorización.
- Se usará `uv`.
- Todas las contraseñas y secretos se proporcionarán mediante variables de entorno.
