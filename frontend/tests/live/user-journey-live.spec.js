const { test, expect } = require('@playwright/test');

async function pause(page, ms = 1800) {
  await page.waitForTimeout(ms);
}

test('live user journey: marketing to signup to app shell', async ({ page }) => {
  test.setTimeout(180000);

  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await pause(page, 2500);

  await page.goto('/features', { waitUntil: 'domcontentloaded' });
  await pause(page);

  await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
  await pause(page);

  await page.goto('/signup', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toBeVisible();
  await pause(page, 2600);

  const uniqueEmail = `live.tester+${Date.now()}@example.com`;

  const nameInput = page.getByTestId('signup-name');
  if (await nameInput.isVisible()) {
    await nameInput.click();
    await pause(page, 900);
    await nameInput.fill('Live Tester');
    await pause(page, 900);
  }

  const emailInput = page.getByTestId('signup-email');
  if (await emailInput.isVisible()) {
    await emailInput.click();
    await pause(page, 900);
    await emailInput.fill(uniqueEmail);
    await pause(page, 900);
  }

  const passwordInput = page.getByTestId('signup-password');
  if (await passwordInput.isVisible()) {
    await passwordInput.click();
    await pause(page, 900);
    await passwordInput.fill('MapleTest123!');
    await pause(page, 1200);
  }

  const submitButton = page.getByTestId('signup-submit');
  if (await submitButton.isVisible()) {
    await submitButton.click();
    await pause(page, 2600);
  }

  // After real signup, expected navigation is onboarding/app.
  await expect(page).toHaveURL(/\/app\/onboarding|\/app|\/login/);

  if ((await page.url()).includes('/login')) {
    const loginEmail = page.getByTestId('login-email');
    const loginPassword = page.getByTestId('login-password');
    const loginSubmit = page.getByTestId('login-submit');
    if (await loginEmail.isVisible()) {
      await loginEmail.fill(uniqueEmail);
      await pause(page, 900);
    }
    if (await loginPassword.isVisible()) {
      await loginPassword.fill('MapleTest123!');
      await pause(page, 900);
    }
    if (await loginSubmit.isVisible()) {
      await loginSubmit.click();
      await pause(page, 2200);
    }
  }

  await page.goto('/app/onboarding', { waitUntil: 'domcontentloaded' });
  await pause(page, 2400);

  await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  await pause(page, 2200);

  await page.goto('/app/jobs', { waitUntil: 'domcontentloaded' });
  await pause(page, 2200);

  await expect(page).toHaveURL(/\/app\/jobs|\/login/);
});
