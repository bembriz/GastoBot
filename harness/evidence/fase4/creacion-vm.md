# Evidence Report — creacion-vm

> **Skill:** `skill-infrastructure` | **Fase:** `fase4`
> **Timestamp:** `2026-07-28T22:51:00` | **Estado:** PASADO

---

## Resumen Ejecutivo

Creacion de la maquina virtual GastosIA sobre Hyper-V en LENOVOSRV. VM Gen 2 con 16 GB RAM estatica, 4 vCPU, VHDX dinamico de 120 GB. Ubuntu Server 24.04.4 LTS instalado via autoinstall con ISO descargado de releases.ubuntu.com/noble. Sistema operativo funcionando con IP estatica 192.168.100.75.

---

## Metricas

| Metrica | Valor |
|---|---|
| Total de verificaciones | 8 |
| Pasadas | 8 |
| Tiempo instalacion | ~10 min |

---

## Especificaciones VM

| Componente | Detalle |
|---|---|
| Nombre | GastosIA |
| Generacion | 2 |
| RAM | 16 GB (static) |
| vCPU | 4 |
| VHDX | 120 GB dynamic (D:\Hyper-V\VirtualMachines\GastosIA\GastosIA.vhdx) |
| ISO | Ubuntu Server 24.04.4 LTS (3.4 GB) |
| Secure Boot | Off |
| Boot order | DVD first |

## Sistema Operativo

| Componente | Detalle |
|---|---|
| OS | Ubuntu 24.04.4 LTS |
| Kernel | 6.8.0-136-generic |
| Hostname | gastos-ia |
| Usuario | gastos-admin |
| IP | 192.168.100.75/24 |
| Disco root | 58 GB (LVM) |
| RAM disponible | 15 GB |

---

*Reporte generado por skill-infrastructure — Gastos IA v1.0*
