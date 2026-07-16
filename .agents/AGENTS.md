# GeoFeedback - Reglas del Agente

## Protocolo de Git y Despliegue

### Rama Principal
- La rama `master` es la rama principal y la única fuente de verdad.
- **NUNCA** hacer push directo a `master`. Todo cambio debe pasar por un Pull Request (PR).

### Flujo de Trabajo Obligatorio
1. **Crear rama**: Para cada cambio, crear una rama con nombre descriptivo usando el formato:
   - `fix/<descripcion>` para correcciones
   - `feat/<descripcion>` para nuevas funcionalidades
   - `refactor/<descripcion>` para refactorizaciones
   - `docs/<descripcion>` para documentación
   - `chore/<descripcion>` para tareas de mantenimiento

2. **Commits**: Usar commits semánticos siguiendo Conventional Commits:
   - `fix(scope): descripción` para correcciones
   - `feat(scope): descripción` para nuevas funcionalidades
   - `refactor(scope): descripción` para refactorizaciones
   - `docs(scope): descripción` para documentación
   - `chore(scope): descripción` para tareas de mantenimiento

3. **Push y PR**: Hacer push de la rama y crear un PR contra `master` usando `gh pr create`.

4. **CI/CD**: Esperar a que todos los checks pasen (CI, CodeQL, Seer Code Review). Si alguno falla, corregir el error y hacer push del fix a la misma rama del PR.

5. **Reviews de Bots**: Si algún bot revisor deja comentarios, resolver cada comentario antes de mergear.

6. **Merge**: Una vez todos los checks pasen y todas las conversaciones estén resueltas, mergear el PR con `gh pr merge --squash --delete-branch`.

7. **Limpieza**: Después del merge, asegurarse de volver a la rama `master` y hacer `git pull`.

### Limpieza de Ramas
- Después de cada merge, la rama del PR debe ser eliminada automáticamente (usar `--delete-branch`).
- No dejar ramas huérfanas en el repositorio remoto.
- Periódicamente ejecutar `git remote prune origin` para limpiar referencias locales a ramas remotas eliminadas.

### Uso de CLI
- Preferir siempre herramientas CLI (`gh`, `git`) sobre el navegador para operaciones de GitHub.
- Usar `$env:GITHUB_TOKEN=''` antes de comandos `gh` si hay conflicto con tokens de entorno.
