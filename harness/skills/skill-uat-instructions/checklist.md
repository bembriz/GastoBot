# Checklist — skill-uat-instructions

## Pre-ejecución
- [ ] PRD completo leído, especialmente §4, §9-17, §33
- [ ] Estructura del manual definida (secciones, orden de casos)
- [ ] Lista de imágenes de `ejemplos/` disponibles confirmada
- [ ] URLs, credenciales de prueba y pre-requisitos documentados
- [ ] Conocimiento de permisos Ruben (admin) vs Esme (estándar)

## Ejecución
- [ ] Caso 1: Login normal (ambos usuarios)
- [ ] Caso 2: Login fallido (contraseña incorrecta)
- [ ] Caso 3: Bloqueo por intentos fallidos
- [ ] Caso 4: Cambio de contraseña inicial
- [ ] Caso 5: Procesamiento de imagen — flujo completo
- [ ] Caso 6: Revisión y edición de gasto
- [ ] Caso 7: Validación de campos obligatorios (botón deshabilitado/habilitado)
- [ ] Caso 8: Sincronización precio_unitario ↔ total
- [ ] Caso 9: Envío a Google Sheets
- [ ] Caso 10: Procesamiento múltiple — Orden FIFO
- [ ] Caso 11: Solo una imagen en ANALIZANDO
- [ ] Caso 12: Duplicado exacto
- [ ] Caso 13: Duplicado probable (advertencia, no bloqueo)
- [ ] Caso 14: HTMX Polling — actualización sin F5
- [ ] Caso 15: Permisos Ruben (admin): ver todo, acceder catálogos
- [ ] Caso 16: Permisos Esme (estándar): ver solo propio, sin catálogos
- [ ] Caso 17: Catálogos CRUD — Categorías
- [ ] Caso 18: Catálogos CRUD — Cuentas
- [ ] Caso 19: Historial — Búsqueda y filtros
- [ ] Caso 20: Historial — Editar y actualizar Sheets
- [ ] Caso 21: Operación sin Internet (PENDIENTE_DE_ENVIO)
- [ ] Caso 22: Cambio de mes en actualización
- [ ] Caso 23: Recuperación tras reinicio
- [ ] Caso 24: Visor de imagen (zoom, rotar, tamaño completo)
- [ ] Caso 25: Manejo de errores (imagen corrupta, archivo no-imagen)

## Post-ejecución
- [ ] Manual guardado en `docs/manual-uat.md`
- [ ] Al menos 20 casos de prueba documentados
- [ ] Cada caso con pre-requisitos, pasos, resultado esperado, pass/fail
- [ ] Plantilla de registro de resultados incluida
- [ ] Cobertura de funcionalidades PRD §9-17 verificada
- [ ] Cobertura de criterios de aceptación PRD §33 verificada
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra schema
- [ ] Métricas documentadas: casos totales, cobertura PRD, tipos de caso
- [ ] Manual autocontenido (no requiere conocimiento previo del sistema)
- [ ] Formato Markdown profesional y legible
