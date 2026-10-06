# Dashboard Bulk Delete Design

## Objetivo

Agregar al dashboard un boton para eliminar registros seleccionados desde PostgreSQL local, sin borrar archivos de imagen y sin ejecutar extraccion IA.

## Alcance

- Reutilizar los checkboxes existentes del dashboard.
- Agregar boton `Eliminar seleccionados` junto a `Enviar seleccionados a Sheets`.
- Pedir confirmacion en navegador antes de eliminar.
- Crear un endpoint bulk-delete que reciba `record_ids`.
- Validar permisos: admin puede eliminar cualquier registro; usuario estandar solo sus propios registros.
- Borrar en PostgreSQL datos dependientes del registro antes del `ExpenseRecord`.
- No tocar imagenes fisicas en SMB/local.
- No invocar Gemini, Kimi, Ollama ni ningun flujo de extraccion.

## Datos Afectados

Para cada registro autorizado se eliminan filas relacionadas en:

- `SheetSync`
- `AuditEvent`
- `ImageFile`
- `ProcessingQueue`
- `ExtractionRun`
- `ExpenseRecord`

El endpoint ignora registros inexistentes con mensaje visible por registro y no detiene toda la operacion.

## UI

El dashboard mantiene una sola seleccion compartida. El boton de envio queda habilitado solo si hay algun registro listo para Sheets. El boton de eliminacion queda habilitado si hay cualquier registro seleccionado no deshabilitado.

Al confirmar la eliminacion, HTMX muestra progreso en `#bulk-result`, limpia la seleccion si la peticion fue exitosa y refresca el listado mediante el polling existente.

## Pruebas

- Unit tests para seleccion vacia, permisos y borrado de relaciones.
- Tests existentes de bulk-send no deben romperse.
- Prueba local con PostgreSQL: insertar registros sinteticos, ejecutar borrado y verificar que no queden filas generadas.
- No se usaran tokens ni imagenes reales para extraccion.

## Fuera de Alcance

- Soft delete.
- Papelera o recuperacion.
- Borrado de archivos fisicos.
- Cambios a Google Sheets para revertir filas ya enviadas.
