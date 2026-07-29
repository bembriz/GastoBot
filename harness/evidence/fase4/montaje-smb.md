# Evidence Report — montaje-smb

> **Skill:** `skill-infrastructure` | **Fase:** `fase4`
> **Timestamp:** `2026-07-28T22:51:00` | **Estado:** PASADO

---

## Resumen Ejecutivo

Montaje de los shares SMB de Ruben y Esme desde el servidor Windows (192.168.100.45) hacia la VM Ubuntu. Se creo el share GastosIA en Windows con las subcarpetas Ruben/pendientes y Esme/pendientes. Los montajes usan CIFS 3.0 con credenciales almacenadas en archivo 0600 y opciones nofail + x-systemd.automount para tolerancia a fallos.

---

## Metricas

| Metrica | Valor |
|---|---|
| Shares creados | 1 (GastosIA) |
| Carpetas usuario | 2 (Ruben, Esme) |
| Montajes exitosos | 2/2 |

---

## Shares

| Usuario | Ruta local | Ruta remota | Version |
|---|---|---|---|
| Ruben | /mnt/smb/Ruben | //192.168.100.45/GastosIA/Ruben | CIFS 3.0 |
| Esme | /mnt/smb/Esme | //192.168.100.45/GastosIA/Esme | CIFS 3.0 |

---

## Verificaciones

| # | Verificacion | Estado |
|---|---|---|
| C41 | cifs-utils instalado | PASADO |
| C42 | Mount points creados | PASADO |
| C43 | Credentials file 0600 | PASADO (/etc/gastos-ia/smb-credentials) |
| C44 | GATE autorizacion fstab | SI |
| C45 | fstab con nofail,automount | PASADO |
| C46 | sudo mount -a exitoso | PASADO |
| C47 | mount grep cifs muestra ambos | PASADO |
| C48 | ls pendientes en ambos shares | PASADO |

---

## Configuracion fstab

```
//192.168.100.45/GastosIA/Ruben /mnt/smb/Ruben cifs credentials=/etc/gastos-ia/smb-credentials,iocharset=utf8,vers=3.0,nofail,x-systemd.automount 0 0
//192.168.100.45/GastosIA/Esme  /mnt/smb/Esme  cifs credentials=/etc/gastos-ia/smb-credentials,iocharset=utf8,vers=3.0,nofail,x-systemd.automount 0 0
```

---

*Reporte generado por skill-infrastructure — Gastos IA v1.0*
