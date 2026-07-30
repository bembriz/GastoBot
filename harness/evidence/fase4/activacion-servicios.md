# Evidencia: Activacion de Servicios

- **Skill:** skill-installer
- **Fase:** 4
- **Timestamp:** 2026-07-29T15:16:00Z
- **Status:** passed

## Resumen

Todos los servicios activados y funcionando. gastos-ia.service corriendo en 127.0.0.1:8000, Caddy reverse proxy HTTPS en gastos.local, Ollama con qwen3-vl:4b.

## Checks

| ID | Descripcion | Status |
|----|------------|--------|
| SRV-01 | systemd service creado | passed |
| SRV-02 | gastos-ia.service active/enabled | passed |
| SRV-03 | Caddy HTTPS proxy | passed |
| SRV-04 | Pagina login renderiza | passed |
| SRV-05 | Ollama qwen3-vl:4b | passed |
| SRV-06 | Caddy TLS configurado | passed |

## Detalles

- **gastos-ia.service:** Type=simple, User=gastos-admin, EnvironmentFile=/etc/gastos-ia/gastos-ia.env
- **Caddy:** gastos.local { reverse_proxy localhost:8000 }
- **Ollama:** localhost:11434, modelo qwen3-vl:4b (3.3 GB)
- **Access:** https://gastos.local (requiere hosts file en cliente Windows)

## Issue Resuelto

Caddy inicialmente solo servia en HTTP (port 80). Fue necesario ejecutar `systemctl reload caddy` para que obtuviera el certificado TLS interno y comenzara a rutear trafico HTTPS correctamente.
