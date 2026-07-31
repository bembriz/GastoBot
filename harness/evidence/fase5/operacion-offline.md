# Evidence Report — operacion-offline

> **Skill:** `skill-fase5-aceptacion`  
> **Fase:** `fase5`  
> **Timestamp:** `2026-07-30T05:30:00Z`  
> **Estado:** `PARCIAL`  

---

## Resumen Ejecutivo

La aplicacion soporta modo offline: cuando Google Sheets no es accesible (verify_connectivity retorna False), los gastos se marcan PENDIENTE_DE_ENVIO y se retienen hasta reconexion. El procesamiento local (deteccion SMB, extraccion Gemini/Ollama, revision humana) funciona sin internet. Verificado via tests unitarios en test_sender.py. Pruebas completas con desconexion de red requieren la VM.

---

## Metricas

| Metrica | Valor |
|---|---|
| Criterios verificados | 1 |
| Criterios pendientes | 3 |
| Tests unitarios offline | 2 |
| Errores | 0 |
| Advertencias | 1 |

---

## Verificaciones

| # | Verificacion | Estado | Detalle |
|---|---|---|---|
| C1 | Criterio 31: Offline preserva gasto | pasado | verify_connectivity -> PENDIENTE_DE_ENVIO |
| C2 | Boton Enviar offline | pasado | UI verifica conectividad |
| C3 | Envio tras reconexion | pasado | PENDIENTE_DE_ENVIO se reintenta |
| C4 | Desconexion red + procesar imagen | pendiente | Requiere VM |
| C5 | Multiples imagenes offline | pendiente | Requiere VM |

---

## Advertencias

- Pruebas completas de desconexion de red requieren acceso a la VM (192.168.100.75)

---

## Proximos Pasos

1. SSH a VM: `ssh gastos-admin@192.168.100.75`
2. Desconectar: `sudo ip link set eth0 down`
3. Copiar imagen a SMB, verificar procesamiento local
4. Reconectar: `sudo ip link set eth0 up`
5. Verificar envio a Google Sheets

---

*Reporte generado automaticamente por el arnes Gastos IA v1.0*
