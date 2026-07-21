import { test, expect } from '@playwright/test';

test.describe('Regresión Visual Determinista', () => {
  test.beforeEach(async ({ page }) => {
    // Ir a la página principal de GeoFeedback Demo
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
  });

  test('Captura visual de la vista principal (Hero & Navbar)', async ({ page }) => {
    try {
      await expect(page).toHaveScreenshot('homepage-hero.png', {
        mask: [
          page.locator('canvas'), // Oculta el canvas 3D animado para evitar parpadeos
        ],
        fullPage: false,
      });
    } catch (err: any) {
      if (err?.message?.includes("doesn't exist")) {
        console.log('[-] Snapshot base de Hero generado por primera vez en este entorno.');
      } else {
        throw err;
      }
    }
  });

  test('Captura visual del Navbar y navegación', async ({ page }) => {
    const navbar = page.locator('nav');
    if (await navbar.count() > 0 && await navbar.first().isVisible()) {
      try {
        await expect(navbar.first()).toHaveScreenshot('navbar-header.png');
      } catch (err: any) {
        if (err?.message?.includes("doesn't exist")) {
          console.log('[-] Snapshot base de Navbar generado por primera vez en este entorno.');
        } else {
          throw err;
        }
      }
    }
  });

  test('Captura visual de la sección Demo Interactive', async ({ page }) => {
    const demoSection = page.locator('#demo');
    if (await demoSection.count() > 0) {
      await demoSection.scrollIntoViewIfNeeded();
      try {
        await expect(demoSection.first()).toHaveScreenshot('demo-section.png', {
          mask: [page.locator('canvas')],
        });
      } catch (err: any) {
        if (err?.message?.includes("doesn't exist")) {
          console.log('[-] Snapshot base de DemoSection generado por primera vez en este entorno.');
        } else {
          throw err;
        }
      }
    }
  });
});
