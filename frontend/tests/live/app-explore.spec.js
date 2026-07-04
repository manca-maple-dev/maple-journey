const { test, expect } = require('@playwright/test');

const routes = [
  '/',
  '/features',
  '/pricing',
  '/login',
  '/signup',
  '/privacy',
  '/terms',
  '/cookies',
  '/disclaimer',
  '/app',
  '/app/onboarding',
  '/app/chat',
  '/app/jobs',
];

test('live explorer: core routes load', async ({ page }) => {
  for (const route of routes) {
    await page.goto(route, { waitUntil: 'domcontentloaded' });
    const currentUrl = page.url();
    if (route.startsWith('/app')) {
      expect(currentUrl).toMatch(/\/app|\/login/);
    } else {
      await expect(page).toHaveURL(new RegExp(route === '/' ? '/$' : route));
    }
    await page.waitForTimeout(600);
  }
});

test('live explorer: navbar and CTA path smoke', async ({ page }) => {
  await page.goto('/', { waitUntil: 'domcontentloaded' });

  const loginLink = page.getByRole('link', { name: /log in|login|sign in/i }).first();
  if (await loginLink.isVisible()) {
    await loginLink.click();
    await expect(page).toHaveURL(/\/login/);
  }

  await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
});