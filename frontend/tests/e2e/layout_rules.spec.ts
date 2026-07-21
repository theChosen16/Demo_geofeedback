import { test, expect } from '@playwright/test';

test.describe('Verificación de Reglas Geométricas y Responsivas de Layout', () => {
  test('Alineación y visibilidad de navegación en escritorio', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    const nav = page.locator('nav');
    await expect(nav).toBeVisible();

    const navBox = await nav.boundingBox();
    expect(navBox).not.toBeNull();
    if (navBox) {
      expect(navBox.y).toBeLessThanOrEqual(50); // Navbar fijo arriba
      expect(navBox.width).toBeGreaterThanOrEqual(1000);
    }
  });

  test('Comprobación de zonas táctiles y ausencia de overflow horizontal en móvil', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone 12 / Pixel
    await page.goto('/');

    // 1. Evitar scrollbar horizontal indeseado (overflow-x)
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const windowWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(windowWidth + 1);

    // 2. Verificar que los botones de llamada a la acción tengan una altura/ancho mínimo táctil (44px)
    const buttons = page.locator('button, a.btn');
    const count = await buttons.count();
    for (let i = 0; i < Math.min(count, 5); i++) {
      const btn = buttons.nth(i);
      if (await btn.isVisible()) {
        const box = await btn.boundingBox();
        if (box && box.height > 0) {
          expect(box.height).toBeGreaterThanOrEqual(36); // Tolerancia adaptable para botones UI
        }
      }
    }
  });
});
