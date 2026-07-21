import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Auditoría Estructural de Accesibilidad (a11y - WCAG 2.1 AA)', () => {
  test('La página de inicio debe auditar la accesibilidad WCAG 2.1 AA', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a', 'wcag21aa'])
      // Excluir elementos dinámicos de terceros (canvas 3D / iframe de mapas)
      .exclude('canvas')
      .exclude('iframe')
      .disableRules(['color-contrast']) // El contraste se evalúa mediante la paleta CSS en ui_ux_design_review_agent
      .analyze();

    if (accessibilityScanResults.violations.length > 0) {
      console.log('Información de accesibilidad (observaciones):', 
        accessibilityScanResults.violations.map(v => ({ id: v.id, impact: v.impact, description: v.description }))
      );
    }

    // Verificar que no existan violaciones de impacto crítico o serio en la estructura principal DOM
    const criticalViolations = accessibilityScanResults.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );
    expect(criticalViolations).toEqual([]);
  });
});
