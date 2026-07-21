import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Auditoría Estructural de Accesibilidad (a11y - WCAG 2.1 AA)', () => {
  test('La página de inicio debe cumplir las normas WCAG 2.1 AA', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a', 'wcag21aa'])
      .analyze();

    // Registrar violaciones si las hubiera en el reporte
    if (accessibilityScanResults.violations.length > 0) {
      console.warn('Violaciones de accesibilidad detectadas:', JSON.stringify(accessibilityScanResults.violations, null, 2));
    }

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('La sección de demostración debe tener etiquetas ARIA y contraste adecuado', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    const demoSection = page.locator('#demo');
    if (await demoSection.count() > 0) {
      const results = await new AxeBuilder({ page })
        .include('#demo')
        .withTags(['wcag2a', 'wcag21aa'])
        .analyze();

      expect(results.violations).toEqual([]);
    }
  });
});
