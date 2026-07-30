# Evidencia: Credenciales Google Sheets

- **Skill:** skill-installer
- **Fase:** 4
- **Timestamp:** 2026-07-29T15:14:00Z
- **Status:** passed

## Resumen

Configuracion de Google Sheets completada. Service account JSON desplegada en la VM y conectividad verificada contra el spreadsheet "Reporte de gastos 2026".

## Checks

| ID | Descripcion | Status |
|----|------------|--------|
| GS-01 | JSON service account copiado | passed |
| GS-02 | Spreadsheet ID configurado | passed |
| GS-03 | Conexion API verificada | passed |
| GS-04 | 11 pestañas accesibles | passed |
| GS-05 | Permisos corregidos (gastos-admin) | passed |

## Detalles

- **Archivo:** /etc/gastos-ia/google-service-account.json
- **Permisos:** 600 gastos-admin:gastos-admin
- **Spreadsheet:** Reporte de gastos 2026
- **Pestañas:** Enero, Febrero, Febrero2, Marzo, Marzo 2, Abril, Mayo, Junio, Julio, correcciones, _Control

## Issue Resuelto

El archivo inicialmente tenia permisos root:root, lo que causaba `PermissionError` al intentar leerlo desde la app (que corre como gastos-admin). Se corrigio con `chown gastos-admin:gastos-admin`.
