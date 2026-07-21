import { test, expect } from '@playwright/test';

test.describe('Regresión Visual Determinista', () => {
  test.beforeEach(async ({ page }) => {
    // Ir a la página principal de GeoFeedback Demo
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
  });

  test('Captura visual de la vista principal (Hero & Navbar)', async ({ page }) => {
    await expect(page).toHaveScreenshot('homepage-hero.png', {
      mask: [
        page.locator('canvas'), // Oculta el canvas 3D animado para evitar parpadeos
      ],
      fullPage: false,
    });
  });

  test('Captura visual del Navbar y navegación', async ({ page, isMobile }) => {
    test.skip(isMobile, 'Navegación de escritorio exclusiva');
    const navbar = page.locator('nav.lg\\:block').first();
    if (await navbar.count() > 0 && await navbar.isVisible()) {
      await expect(navbar).toHaveScreenshot('navbar-header.png');
    }
  });

  test('Captura visual de la sección Demo Interactive', async ({ page }) => {
    const demoSection = page.locator('#demo').first();
    if (await demoSection.count() > 0) {
      await demoSection.scrollIntoViewIfNeeded();
      await expect(demoSection).toHaveScreenshot('demo-section.png', {
        mask: [page.locator('canvas')],
      });
    }
  });
});
