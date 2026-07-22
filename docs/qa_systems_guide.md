# Guía de Uso: Sistema Multi-Capa de QA, Evaluación Visual y Auditoría UI/UX

Esta guía documenta la infraestructura de Aseguramiento de Calidad (QA) integrada en **GeoFeedback Demo**.

---

## Estructura del Sistema Multi-Capa

El marco de calidad opera en 4 niveles complementarios:

1. **Agente IA de Auditoría Heurística & Observador Gemini (gemini-2.5-flash-lite):**
   - **Herramientas:** `scripts/qa/ui_ux_design_review_agent.py`, `scripts/qa/uisentinel_check.js` & `scripts/qa/gemini_qa_observer.py`
   - **Objetivo:** Inspeccionar el código frontend (TSX/CSS) en busca de jerarquía visual, atributos ARIA, contrastes y zonas táctiles responsivas. El **Observador Gemini** toma notas continuas de la telemetría de todos los niveles.
   - **Entregables:** Informes en `.agents/ui_reports/` (`ui_analysis_report.md`, `color_palettes_report.md`, `animations_report.md`, `gemini_qa_observer_notes.md`).

2. **Regresión Visual Determinista (Playwright):**
   - **Configuración:** `frontend/playwright.config.ts`
   - **Pruebas:** `frontend/tests/e2e/visual_regression.spec.ts`
   - **Características:** Comparación de mapas de bits con `pixelmatch`, enmascaramiento dinámico de elementos cambiantes (mapas, animaciones) y soporte multi-dispositivo (Escritorio HD, Tablet, Móvil).

3. **Verificación de Reglas Geométricas & Layout:**
   - **Pruebas:** `frontend/tests/e2e/layout_rules.spec.ts`
   - **Objetivo:** Ratificar alineaciones, márgenes y ausencia de desbordamiento horizontal (`overflow-x`) en resoluciones móviles sin depender de frágiles capturas de píxeles.

4. **Accesibilidad Estructural (WCAG 2.1 AA) & Rendimiento (Lighthouse CI):**
   - **Accesibilidad:** `frontend/tests/e2e/accessibility.spec.ts` usando `@axe-core/playwright`.
   - **Rendimiento:** Configuración `.lighthouserc.json` que valida presupuestos Core Web Vitals (LCP, CLS, FCP) en CI/CD.

---

## Flujos de Trabajo y Comandos

### 1. Ejecución Local del Agente Heurístico UI/UX
```bash
python scripts/qa/ui_ux_design_review_agent.py
node scripts/qa/uisentinel_check.js
```

### 2. Ejecución Local de Pruebas Visuales y de Accesibilidad (Playwright)
```bash
cd frontend
npm run test:e2e
```
Para ver el reporte HTML interactivo tras las pruebas:
```bash
npx playwright show-report
```

### 3. Actualización de Instantáneas (Snapshots) de Referencia Visual
Si realizaste un cambio de diseño intencional y deseas actualizar las imágenes base de comparación:

- **Localmente:**
  ```bash
  cd frontend
  npm run test:e2e:update-snapshots
  ```
- **Vía GitHub Actions (ChatOps):**
  Escribe `/approve-snapshots` en los comentarios de tu Pull Request. El flujo `.github/workflows/approve_snapshots.yml` ejecutará la actualización dentro de Docker y enviará un commit automático con las capturas aprobadas.

### 4. Auditoría de Rendimiento Web (Lighthouse CI)
```bash
cd frontend
npm run build
npx lighthouserc run
```
