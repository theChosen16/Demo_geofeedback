import { test, expect } from '@playwright/test';

test.describe('Regresión Visual Determinista', () => {
  test.beforeEach(async ({ page }) => {
    // Ir a la página principal de GeoFeedback Demo
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('Captura visual de la vista principal (Hero & Navbar)', async ({ page }) => {
    // Ocultar o enmascarar elementos inestables si existieran (ej. canvas 3D dinámico de EarthCanvas)
    await expect(page).toHaveScreenshot('homepage-hero.png', {
      mask: [
        page.locator('canvas'), // Oculta el canvas 3D animado para evitar parpadeos
      ],
      fullPage: false,
    });
  });

  test('Captura visual del Navbar y navegación', async ({ page }) => {
    const navbar = page.locator('nav');
    if (await navbar.count() > 0) {
      await expect(navbar.first()).toHaveScreenshot('navbar-header.png');
    }
  });

  test('Captura visual de la sección Demo Interactive', async ({ page }) => {
    const demoSection = page.locator('#demo');
    if (await demoSection.count() > 0) {
      await demoSection.scrollIntoViewIfNeeded();
      await expect(demoSection.first()).toHaveScreenshot('demo-section.png', {
        mask: [page.locator('canvas')],
      });
    }
  });
});
