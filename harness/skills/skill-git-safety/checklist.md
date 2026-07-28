# Checklist — skill-git-safety

## Pre-ejecución
- [ ] `gitleaks` instalado y funcional
- [ ] Repositorio Git inicializado
- [ ] Puerta de calidad (`skill-quality-gate`) aprobada
- [ ] `.gitignore` presente y configurado según PRD §26
- [ ] `.gitleaks.toml` configurado si es necesario (allowlist)

## Ejecución
- [ ] Rama verificada: NO es `main`
- [ ] Rama actual es `arnes` o rama de feature
- [ ] `gitleaks detect --source .` ejecutado — código 0 (sin leaks)
- [ ] Si hay leaks: identificados, clasificados, plan de remediación definido
- [ ] `git diff --stat` y `git diff --stat --cached` analizados
- [ ] Archivos clasificados por tipo (skills, source, tests, config, docs, infra)
- [ ] Archivos prohibidos verificados: .env, credentials/, secrets/, .pem, .key
- [ ] Sin imágenes reales, logs, backups, o modelos en los cambios
- [ ] Diff ejecutivo generado con el formato exacto:
  ```
  ## Resumen de Diff
  **Branch:** {branch}
  **Archivos modificados:** {N}
  **Líneas agregadas:** +{N}
  **Líneas eliminadas:** -{N}

  ### Archivos por tipo
  ...

  ### Archivos modificados
  | Archivo | Tipo | Cambios |
  ...

  ### Escaneo de secretos
  ...

  ### Mensaje de commit propuesto
  ...

  ¿Autorizas commit? (AUTORIZO COMMIT)
  ```
- [ ] Mensaje de commit propuesto sigue formato convencional (`tipo(scope): descripción`)
- [ ] Resumen presentado al usuario
- [ ] Esperando autorización explícita

## Post-ejecución (solo si autorizado)
- [ ] Usuario escribió "AUTORIZO COMMIT"
- [ ] Archivos correctos en staged (`git add` solo lo autorizado)
- [ ] `git commit` ejecutado exitosamente
- [ ] Hash del commit registrado
- [ ] Si hubo push: autorización independiente "AUTORIZO PUSH" recibida
- [ ] Si hubo push: `git push` ejecutado exitosamente
- [ ] Evidencia JSON generada en `harness/evidence/{phase}/`
- [ ] Evidencia MD generada en `harness/evidence/{phase}/`
- [ ] Evidencia JSON válida contra schema
- [ ] Hash del commit, archivos, y resultado de gitleaks documentados en evidencia
