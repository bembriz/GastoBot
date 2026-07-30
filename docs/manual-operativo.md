# Manual Operativo — Gastos IA

## Indice
1. [Requisitos del Cliente](#requisitos)
2. [Inicio de Sesion](#login)
3. [Procesar un Ticket](#procesar)
4. [Revisar y Completar](#revisar)
5. [Enviar a Google Sheets](#enviar)
6. [Catalogos (admin)](#catalogos)
7. [Historial (admin)](#historial)
8. [Resolucion de Problemas](#problemas)

---

## Requisitos del Cliente {#requisitos}

En tu PC Windows, agregar esta linea al archivo hosts:

```
# Editar como Administrador: C:\Windows\System32\drivers\etc\hosts
192.168.100.75  gastos.local
```

Abrir el navegador en `https://gastos.local`. Aceptar la advertencia de seguridad del certificado (es local, seguro).

---

## Inicio de Sesion {#login}

1. Abrir `https://gastos.local`
2. Usuario: `Ruben` o `Esme`
3. Contrasena inicial: `260729@GastosXuum`
4. Clic en **Entrar**

**Ruben** (admin):
- Ve todos los comprobantes de Ruben y Esme
- Accede a Catalogos e Historial

**Esme** (standard):
- Solo ve sus propios comprobantes
- No tiene acceso a catalogos ni historial

---

## Procesar un Ticket {#procesar}

1. Copia la imagen del ticket/comprobante en la carpeta de red:
   - **Ruben**: `\\192.168.100.45\GastosIA\Ruben\pendientes`
   - **Esme**: `\\192.168.100.45\GastosIA\Esme\pendientes`

2. Formatos aceptados: `.jpg`, `.jpeg`, `.png`, `.webp` (maximo 15 MB)

3. En menos de 30 segundos, el ticket aparecera en el dashboard con los campos extraidos automaticamente:
   - Fecha del gasto
   - Monto
   - Banco emisor
   - Descripcion (concepto)
   - Tipo de transaccion (Transferencia / Credito)

---

## Revisar y Completar {#revisar}

1. En el dashboard, clic en **Revisar** junto al comprobante
2. Verifica que los campos extraidos sean correctos:
   - **Fecha**: ajustar si es necesario
   - **Importe**: corregir si el OCR confundio el signo `$` con un `8`
   - **Banco**: verificar que sea el banco emisor correcto
   - **Descripcion del ticket**: editar si el concepto no es claro
3. Completa los campos obligatorios:
   - **Grupo**: codigo del proyecto (ej: VAL, OP, PSAV, BORAMAR)
   - **Cuenta**: seleccionar del catalogo
   - **Categoria**: se filtra automaticamente segun la cuenta elegida
4. La **Descripcion final** se genera automaticamente: `GRUPO--concepto`
5. Clic en **Guardar**

El estado cambia:
- `REQUIERE_REVISION` → faltan campos por completar
- `PENDIENTE_DE_ENVIO` → todos los campos listos para enviar

---

## Enviar a Google Sheets {#enviar}

### Envio individual:
1. Tener todos los campos completos (estado `PENDIENTE_DE_ENVIO`)
2. Clic en **Guardar** en la pantalla de revision

### Envio masivo:
1. En el dashboard, marcar los checkboxes de los registros completos
2. Solo se pueden seleccionar registros con todos los campos llenos
3. Clic en **Enviar seleccionados a Sheets**
4. Los registros se envian a la pestana del mes correspondiente en Google Sheets

Despues del envio:
- El registro pasa a estado `ENVIADO`
- La imagen se mueve a `procesados/` automaticamente

---

## Catalogos (Solo Admin) {#catalogos}

Accesible desde el menu superior (solo Ruben):

1. Clic en **Catalogos**
2. Gestionar **Cuentas** (ej: 10000008 Gastos Operativos)
3. Gestionar **Categorias** vinculadas a cada cuenta
4. Las categorias se filtran automaticamente al seleccionar cuenta en el formulario

---

## Historial (Solo Admin) {#historial}

Accesible desde el menu superior (solo Ruben):

1. Clic en **Historial**
2. Buscar por fecha, banco, grupo, usuario
3. Ver todos los registros historicos (incluyendo ENVIADO)
4. Editar un registro enviado actualiza Google Sheets automaticamente

---

## Resolucion de Problemas {#problemas}

### El ticket no aparece en el dashboard
- Verificar que la imagen este en la carpeta `pendientes` correcta
- Formatos validos: .jpg, .jpeg, .png, .webp
- Tiempo de espera: hasta 60 segundos (deteccion + analisis Gemini)

### La imagen aparece como "Imagen no disponible"
- Recargar la pagina de revision
- Verificar que el archivo no haya sido movido de `pendientes/`

### El monto es incorrecto
- Editar manualmente en el formulario de revision
- Guardar; el nuevo valor se usara para Sheets

### No se puede enviar a Sheets (boton deshabilitado)
- Verificar que todos los campos esten completos:
  - Fecha ✓
  - Importe ✓
  - Banco ✓
  - Grupo ✓
  - Cuenta ✓
  - Categoria ✓
- El estado debe ser `PENDIENTE_DE_ENVIO`

### Google Sheets no recibe los datos
- Verificar conexion a internet de la VM
- Reintentar; los registros en `PENDIENTE_DE_ENVIO` se pueden enviar cuando la conexion se restablezca

### La aplicacion no carga (https://gastos.local)
- Verificar que la VM este encendida (Hyper-V en el servidor)
- Verificar que el archivo hosts en Windows tenga la entrada correcta
- Contactar al administrador del sistema

---

## Estados de un Comprobante

| Estado | Significado |
|--------|-------------|
| DETECTADO | Imagen encontrada en carpeta |
| EN_COLA | Esperando turno de analisis |
| ANALIZANDO | Gemini analizando la imagen |
| REQUIERE_REVISION | Esperando que completes campos |
| PENDIENTE_DE_ENVIO | Listo para enviar a Sheets |
| ENVIANDO | Enviandose a Google Sheets |
| ENVIADO | Ya registrado en Sheets |
| DUPLICADO_EXACTO | Imagen ya procesada antes |
| ERROR_PROCESAMIENTO | Fallo el analisis de la imagen |
