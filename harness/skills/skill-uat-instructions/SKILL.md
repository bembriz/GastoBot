# Skill: skill-uat-instructions

## Identity
Eres un technical writer y QA lead especializado en documentación de pruebas de aceptación de usuario (UAT). Creas manuales HITL (Human-In-The-Loop) claros, detallados y accionables para que usuarios no técnicos (Ruben y Esme) puedan validar el sistema paso a paso. Cada instrucción incluye entradas, salidas esperadas y criterios de aprobación/rechazo.

## Context
Esta skill produce el manual de UAT para Gastos IA. El manual cubre cada funcionalidad visible al usuario descrita en el PRD (§9-17, §33). Sirve como guía para la Fase 5 (Aceptación) donde Ruben y Esme ejecutarán pruebas funcionales reales contra el sistema desplegado.

El manual debe ser autocontenido: cualquier persona con acceso a la aplicación y este documento debe poder ejecutar todas las pruebas sin conocimiento previo del sistema. Se entrega como un archivo Markdown bien estructurado con tablas, listas numeradas y criterios claros de pass/fail.

## Preconditions
- PRD v1.2 leído y comprendido (secciones §9-17, §33)
- Conocimiento de los dos perfiles de usuario: Ruben (admin) y Esme (estándar)
- Conocimiento de los estados de gasto definidos en PRD §17
- Directorio `ejemplos/` con imágenes de prueba disponibles
- Conocimiento de los campos del formulario (PRD §11)
- Conocimiento de los endpoints y flujos de la interfaz

## Execution

### Step 1: Estructurar el manual
Crear el archivo `docs/manual-uat.md` con la siguiente estructura:

1. Portada: título, versión, fecha, autores
2. Introducción: propósito, audiencia, pre-requisitos
3. Preparación del entorno de prueba
4. Casos de prueba (secciones numeradas)
5. Registro de resultados (plantilla de tabla)
6. Resumen de aprobación

### Step 2: Documentar pre-requisitos y preparación
Incluir sección con:
- URLs de acceso (https://gastos.local)
- Credenciales de prueba para ambos usuarios
- Requisitos de navegador (Chrome/Firefox/Edge actualizado)
- Lista de imágenes de prueba a usar de `ejemplos/` (nombre de archivo y breve descripción)
- Estado esperado de la base de datos al inicio
- Cómo restaurar el estado inicial si es necesario
- Nota: contraseñas son de prueba, NO las reales

### Step 3: Documentar casos de prueba

**Caso 1: Login — Flujo normal**
- Pre-requisito: Usuario registrado, contraseña inicial configurada
- Paso 1: Navegar a https://gastos.local/login
- Paso 2: Ingresar "ruben" en campo Usuario
- Paso 3: Ingresar contraseña de prueba en campo Contraseña
- Paso 4: Clic en "Iniciar sesión"
- Resultado esperado: Redirigir a /expenses, ver lista de gastos, nombre de usuario visible en barra superior
- Criterio pass: Redirección exitosa, sin mensajes de error
- Criterio fail: Mensaje de error, permanece en login, error 500

**Caso 2: Login — Contraseña incorrecta**
- Paso 1-3: Ídem con contraseña incorrecta
- Paso 4: Clic en "Iniciar sesión"
- Resultado esperado: Mensaje "Usuario o contraseña incorrectos", permanecer en página de login
- Criterio pass: Mensaje de error visible, no redirige
- Criterio fail: Redirige con credenciales incorrectas, o error 500

**Caso 3: Login — Bloqueo por intentos**
- Pre-requisito: Contador de intentos en 0
- Paso: Repetir login fallido 5 veces consecutivas
- Resultado esperado: Tras el 5º intento, mensaje "Cuenta bloqueada temporalmente. Intente de nuevo en X minutos"
- Criterio pass: Bloqueo aplicado, intentos adicionales rechazados incluso con contraseña correcta
- Criterio fail: Permite intentos ilimitados, o no muestra mensaje de bloqueo

**Caso 4: Login — Ambos usuarios**
- Repetir Caso 1 para Esme (usuario "esme")
- Verificar que ambos pueden iniciar sesión independientemente
- Verificar que las sesiones son independientes (logout de uno no afecta al otro)

**Caso 5: Procesamiento de imagen — Flujo completo (Ruben)**
- Pre-requisito: Sesión iniciada como Ruben
- Paso 1: Copiar imagen `ejemplos/ticket_001.jpg` a `\\SERVIDOR\GastosIA\Ruben\pendientes\`
- Paso 2: Esperar hasta 15 segundos para detección
- Paso 3: Verificar que la imagen aparece en la lista de pendientes con estado DETECTADO o EN_COLA
- Paso 4: Esperar transiciones vía HTMX polling: EN_COLA → ANALIZANDO → LISTO_PARA_REVISION
- Paso 5: Clic en la imagen para abrir el visor de revisión
- Paso 6: Verificar que la imagen es visible en el visor
- Paso 7: Verificar que los campos extraídos aparecen: fecha, monto, descripción, banco, tipo
- Paso 8: Verificar indicadores de confianza (alta/media/baja) junto a cada campo
- Criterio pass: Imagen procesada, datos extraídos, confianza mostrada
- Criterio fail: Imagen no aparece, no se procesa, error en extracción, campos vacíos

**Caso 6: Revisión y edición de gasto**
- Paso 1: En el visor de revisión, modificar fecha usando el calendario
- Paso 2: Ingresar grupo (ej. "VAL")
- Paso 3: Modificar descripción si es necesario
- Paso 4: Seleccionar categoría del dropdown
- Paso 5: Seleccionar cuenta del dropdown
- Paso 6: Verificar que "Descripción final" muestra: GRUPO-Consecutivo-Descripción
- Paso 7: Modificar precio unitario → verificar que total cambia igual
- Paso 8: Modificar total → verificar que precio unitario cambia igual
- Paso 9: Seleccionar banco y tipo de transacción
- Resultado esperado: Todos los campos editables responden, descripción final se actualiza, precio/total sincronizados
- Criterio pass: Campos funcionan, sincronización correcta
- Criterio fail: Campos no editables, descripción final no se actualiza, precio/total no sincronizados

**Caso 7: Validación de campos obligatorios**
- Paso 1: Abrir gasto en revisión
- Paso 2: Dejar campo "Grupo" vacío
- Paso 3: Verificar que botón "Enviar a Google Sheets" está deshabilitado
- Paso 4: Llenar grupo → botón sigue deshabilitado si falta otro campo
- Paso 5: Llenar todos los campos obligatorios (fecha, grupo, descripción, categoría, cuenta, precio, banco, tipo)
- Paso 6: Verificar que botón se habilita
- Criterio pass: Botón inhabilitado con campos faltantes, habilitado con todos
- Criterio fail: Botón habilitado con campos faltantes, o inhabilitado con todos los campos

**Caso 8: Envío a Google Sheets**
- Pre-requisito: Gasto en LISTO_PARA_REVISION, todos los campos llenos, Internet disponible
- Paso 1: Clic en "Enviar a Google Sheets"
- Paso 2: Esperar indicador de envío (spinner o mensaje "Enviando...")
- Paso 3: Verificar transición de estado: ENVIANDO → ENVIADO
- Paso 4: Verificar que la imagen se movió a `procesados/YYYY/MM/`
- Paso 5: Abrir Google Sheets y verificar que el registro aparece en la pestaña mensual correcta
- Criterio pass: Estado ENVIADO, imagen movida, registro en Sheets
- Criterio fail: Error en envío, estado ERROR_SHEETS, imagen no movida, registro no aparece

**Caso 9: Procesamiento múltiple — Orden FIFO**
- Paso 1: Copiar 5 imágenes a `pendientes/` (anotar orden de copia)
- Paso 2: Verificar que aparecen en la lista de pendientes en orden de llegada
- Paso 3: Verificar que solo UNA imagen está en estado ANALIZANDO
- Paso 4: Verificar que las demás están en EN_COLA
- Paso 5: Esperar a que la primera termine → verificar que la siguiente pasa a ANALIZANDO
- Paso 6: Repetir hasta que todas estén procesadas
- Criterio pass: Orden FIFO respetado, solo una en ANALIZANDO
- Criterio fail: Múltiples en ANALIZANDO, orden incorrecto, imágenes saltadas

**Caso 10: Duplicado exacto**
- Paso 1: Procesar imagen `ejemplos/ticket_001.jpg`
- Paso 2: Esperar a que llegue a LISTO_PARA_REVISION o ENVIADO
- Paso 3: Copiar la misma imagen otra vez a `pendientes/`
- Paso 4: Verificar que el estado es DUPLICADO_EXACTO
- Paso 5: Verificar mensaje indicando el registro original
- Paso 6: Verificar que la imagen duplicada se movió a `errores/duplicados/`
- Criterio pass: DUPLICADO_EXACTO, referencia al original, archivo movido
- Criterio fail: Procesa el duplicado como nuevo, no detecta duplicado

**Caso 11: Duplicado probable**
- Pre-requisito: Dos imágenes diferentes del mismo ticket (misma fecha, monto, banco)
- Paso 1: Procesar primera imagen → llega a LISTO_PARA_REVISION
- Paso 2: Enviar primera imagen
- Paso 3: Procesar segunda imagen → debe mostrar advertencia de duplicado probable
- Paso 4: Verificar que la advertencia es visible pero no bloquea
- Paso 5: Confirmar envío manualmente → debe permitir
- Criterio pass: Advertencia mostrada, envío permitido con confirmación
- Criterio fail: Bloquea como duplicado exacto, o no muestra advertencia

**Caso 12: HTMX Polling — Actualización en tiempo real**
- Paso 1: Abrir página de gastos
- Paso 2: Copiar una imagen nueva a `pendientes/`
- Paso 3: Sin presionar F5, esperar máximo 10 segundos
- Paso 4: Verificar que la nueva imagen aparece en la lista
- Paso 5: Verificar que el estado cambia de EN_COLA → ANALIZANDO sin recargar
- Paso 6: Verificar que el estado cambia a LISTO_PARA_REVISION sin recargar
- Criterio pass: Todos los cambios visibles sin intervención manual
- Criterio fail: Requiere F5 para ver cambios, polling no funciona

**Caso 13: Permisos — Ruben (admin)**
- Paso 1: Login como Ruben
- Paso 2: Verificar que ve gastos de Ruben Y Esme
- Paso 3: Verificar columna "Propietario" visible
- Paso 4: Navegar a Catálogos → Categorías (debe ser accesible)
- Paso 5: Navegar a Catálogos → Cuentas (debe ser accesible)
- Paso 6: Navegar a Catálogos → Usuarios (debe ser accesible)
- Criterio pass: Ve todos los gastos, accede a todos los catálogos
- Criterio fail: Solo ve gastos propios, catálogos no accesibles

**Caso 14: Permisos — Esme (estándar)**
- Paso 1: Login como Esme
- Paso 2: Verificar que SOLO ve sus propios gastos
- Paso 3: Verificar que NO ve columna "Propietario"
- Paso 4: Intentar acceder a /catalogs → debe mostrar 403 o redirigir
- Paso 5: Verificar que no hay enlaces a catálogos en la navegación
- Criterio pass: Solo ve gastos propios, sin acceso a catálogos
- Criterio fail: Ve gastos de Ruben, accede a catálogos

**Caso 15: Catálogos — CRUD Categorías (Ruben)**
- Paso 1: Login como Ruben → navegar a Catálogos → Categorías
- Paso 2: Crear nueva categoría "Test Categoría UAT" → verificar que aparece en lista
- Paso 3: Editar categoría → cambiar nombre a "Test Categoría Modificada" → verificar cambio
- Paso 4: Desactivar categoría → verificar que no aparece en dropdown de revisión
- Paso 5: Reactivar categoría → verificar que reaparece en dropdown
- Criterio pass: CRUD completo funcional
- Criterio fail: Error al crear/editar/desactivar

**Caso 16: Historial — Búsqueda y filtros**
- Paso 1: Login como Ruben → navegar a Historial
- Paso 2: Buscar por rango de fechas → verificar resultados filtrados
- Paso 3: Buscar por banco (ej. "NU") → verificar resultados
- Paso 4: Buscar por grupo (ej. "VAL") → verificar resultados
- Paso 5: Filtrar por usuario (Ruben) → verificar solo gastos de Ruben
- Paso 6: Combinar filtros (fecha + banco) → verificar intersección
- Criterio pass: Filtros funcionan individualmente y combinados
- Criterio fail: Filtros no aplican, resultados incorrectos

**Caso 17: Historial — Editar y actualizar Sheets**
- Paso 1: En historial, localizar gasto enviado previamente
- Paso 2: Clic en "Editar" → verificar formulario de edición
- Paso 3: Cambiar monto y grupo
- Paso 4: Clic en "Actualizar en Google Sheets"
- Paso 5: Verificar que Sheets refleja el cambio
- Paso 6: Verificar que _Control se actualizó
- Criterio pass: Cambios reflejados en Sheets y _Control
- Criterio fail: Error al actualizar, datos inconsistentes

**Caso 18: Operación sin Internet**
- Pre-requisito: Desconectar Internet (o simular) después del procesamiento
- Paso 1: Procesar imagen normalmente (extracción local funciona sin Internet)
- Paso 2: Llenar todos los campos en revisión
- Paso 3: Clic en "Enviar a Google Sheets"
- Paso 4: Verificar que el estado cambia a PENDIENTE_DE_ENVIO
- Paso 5: Verificar mensaje "Sin conexión. El gasto se enviará cuando haya Internet."
- Paso 6: Restaurar Internet
- Paso 7: Clic en "Reenviar" o el botón de reintento
- Paso 8: Verificar que el estado cambia a ENVIADO
- Criterio pass: PENDIENTE_DE_ENVIO sin Internet, envío exitoso al reconectar
- Criterio fail: Error al procesar sin Internet, datos perdidos

**Caso 19: Cambio de mes en actualización**
- Pre-requisito: Gasto enviado en pestaña "Julio-26", editarlo cambiando fecha a "Agosto-26"
- Paso 1: Desde historial, editar gasto enviado de Julio
- Paso 2: Cambiar fecha a un día de Agosto
- Paso 3: Guardar y actualizar en Sheets
- Paso 4: Verificar que el registro desaparece de pestaña Julio-26
- Paso 5: Verificar que aparece en pestaña Agosto-26 (se crea si no existe)
- Criterio pass: Registro movido correctamente entre pestañas
- Criterio fail: Registro duplicado, no movido, o error

**Caso 20: Recuperación tras reinicio**
- Pre-requisito: 3 imágenes en EN_COLA, 1 en ANALIZANDO
- Paso 1: Reiniciar el servidor (simular crash)
- Paso 2: Esperar a que la aplicación reinicie
- Paso 3: Verificar que la imagen que estaba en ANALIZANDO ahora está en EN_COLA
- Paso 4: Verificar que el worker retoma el procesamiento
- Paso 5: Verificar que las 4 imágenes se procesan sin duplicados
- Criterio pass: Todas procesadas, sin duplicados, sin pérdida
- Criterio fail: Imágenes perdidas, duplicadas, o en estado incorrecto

### Step 4: Crear plantilla de registro de resultados
Incluir al final del manual una tabla como:
```
| # | Caso | Ejecutado por | Fecha | Resultado | Observaciones |
|---|------|--------------|-------|-----------|---------------|
| 1 | Login normal | | | PASS / FAIL | |
| 2 | Login fallido | | | PASS / FAIL | |
| ... | ... | | | PASS / FAIL | |
```

### Step 5: Generar evidencia
1. Confirmar que `docs/manual-uat.md` existe y está completo
2. Crear evidencia JSON y MD en `harness/evidence/{phase}/`
3. Incluir métricas:
   - Total de casos de prueba documentados
   - Cobertura de funcionalidades del PRD
   - Cobertura de criterios de aceptación del PRD §33
   - Casos por tipo: funcional, permiso, error, concurrencia, recuperación

## Artifacts
- `docs/manual-uat.md` — Manual UAT completo
- `harness/evidence/{phase}/uat-instructions-{timestamp}.json`
- `harness/evidence/{phase}/uat-instructions-{timestamp}.md`

## Quality Criteria
- Manual cubre >= 20 casos de prueba distintos
- Cada caso tiene: pre-requisitos, pasos numerados, resultado esperado, criterio pass/fail
- Cubiertos todos los flujos de PRD §9 (Ingreso, Revisión, Envío)
- Cubiertos todos los controles de PRD §11 (campos, sincronización, obligatoriedad)
- Cubiertos permisos de ambos roles (PRD §4)
- Cubierto HTMX Polling (PRD §10.2.1)
- Cubiertos duplicados exacto y probable (PRD §15)
- Cubierta operación offline (PRD §9.5)
- Cubierta recuperación tras reinicio
- Cubiertos catálogos CRUD
- Cubierto historial con búsqueda, filtros y actualización
- Plantilla de registro de resultados incluida
- Manual autocontenido (no requiere conocimiento previo)
- Formato Markdown profesional con tablas y numeración

## Edge Cases
- **Imágenes de `ejemplos/` no disponibles:** listar nombres esperados para que el usuario las busque o las genere
- **Google Sheets no accesible durante UAT:** incluir casos que solo requieren procesamiento local
- **Ollama no responde:** documentar cómo verificar `ollama ps` y reiniciar el servicio
- **Un solo usuario disponible:** marcar casos que requieren ambos como "No ejecutable" en la plantilla
- **Datos de prueba inconsistentes:** incluir script o instrucciones para resetear la base de datos
- **HTMX polling no visible a simple vista:** instruir abrir DevTools → Network para ver requests periódicos

## References
- PRD §4 (Usuarios y permisos)
- PRD §9 (Flujo funcional)
- PRD §10 (Interfaz web), §10.2.1 (HTMX Polling)
- PRD §11 (Campos visibles y reglas)
- PRD §12 (Descripción y consecutivo)
- PRD §13 (Google Sheets)
- PRD §14 (Actualización de registros)
- PRD §15 (Duplicados)
- PRD §16 (Confianza)
- PRD §17 (Estados)
- PRD §33 (Criterios de aceptación)
- Related skills: `skill-fase5-aceptacion`, `skill-e2e-tests`
