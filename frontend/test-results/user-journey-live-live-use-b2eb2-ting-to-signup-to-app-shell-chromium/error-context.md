# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: user-journey-live.spec.js >> live user journey: marketing to signup to app shell
- Location: tests\live\user-journey-live.spec.js:7:1

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
Call log:
  - navigating to "http://localhost:3000/", waiting until "domcontentloaded"

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e6]:
    - heading "This site can’t be reached" [level=1] [ref=e7]
    - paragraph [ref=e8]:
      - strong [ref=e9]: localhost
      - text: refused to connect.
    - generic [ref=e10]:
      - paragraph [ref=e11]: "Try:"
      - list [ref=e12]:
        - listitem [ref=e13]: Checking the connection
        - listitem [ref=e14]:
          - link "Checking the proxy and the firewall" [ref=e15] [cursor=pointer]:
            - /url: "#buttons"
    - generic [ref=e16]: ERR_CONNECTION_REFUSED
  - generic [ref=e17]:
    - button "Reload" [ref=e19] [cursor=pointer]
    - button "Details" [ref=e20] [cursor=pointer]
```

# Test source

```ts
  1  | const { test, expect } = require('@playwright/test');
  2  | 
  3  | async function pause(page, ms = 1800) {
  4  |   await page.waitForTimeout(ms);
  5  | }
  6  | 
  7  | test('live user journey: marketing to signup to app shell', async ({ page }) => {
  8  |   test.setTimeout(180000);
  9  | 
> 10 |   await page.goto('/', { waitUntil: 'domcontentloaded' });
     |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/
  11 |   await pause(page, 2500);
  12 | 
  13 |   await page.goto('/features', { waitUntil: 'domcontentloaded' });
  14 |   await pause(page);
  15 | 
  16 |   await page.goto('/pricing', { waitUntil: 'domcontentloaded' });
  17 |   await pause(page);
  18 | 
  19 |   await page.goto('/signup', { waitUntil: 'domcontentloaded' });
  20 |   await expect(page.locator('body')).toBeVisible();
  21 |   await pause(page, 2600);
  22 | 
  23 |   const uniqueEmail = `live.tester+${Date.now()}@example.com`;
  24 | 
  25 |   const nameInput = page.getByTestId('signup-name');
  26 |   if (await nameInput.isVisible()) {
  27 |     await nameInput.click();
  28 |     await pause(page, 900);
  29 |     await nameInput.fill('Live Tester');
  30 |     await pause(page, 900);
  31 |   }
  32 | 
  33 |   const emailInput = page.getByTestId('signup-email');
  34 |   if (await emailInput.isVisible()) {
  35 |     await emailInput.click();
  36 |     await pause(page, 900);
  37 |     await emailInput.fill(uniqueEmail);
  38 |     await pause(page, 900);
  39 |   }
  40 | 
  41 |   const passwordInput = page.getByTestId('signup-password');
  42 |   if (await passwordInput.isVisible()) {
  43 |     await passwordInput.click();
  44 |     await pause(page, 900);
  45 |     await passwordInput.fill('MapleTest123!');
  46 |     await pause(page, 1200);
  47 |   }
  48 | 
  49 |   const submitButton = page.getByTestId('signup-submit');
  50 |   if (await submitButton.isVisible()) {
  51 |     await submitButton.click();
  52 |     await pause(page, 2600);
  53 |   }
  54 | 
  55 |   // After real signup, expected navigation is onboarding/app.
  56 |   await expect(page).toHaveURL(/\/app\/onboarding|\/app|\/login/);
  57 | 
  58 |   if ((await page.url()).includes('/login')) {
  59 |     const loginEmail = page.getByTestId('login-email');
  60 |     const loginPassword = page.getByTestId('login-password');
  61 |     const loginSubmit = page.getByTestId('login-submit');
  62 |     if (await loginEmail.isVisible()) {
  63 |       await loginEmail.fill(uniqueEmail);
  64 |       await pause(page, 900);
  65 |     }
  66 |     if (await loginPassword.isVisible()) {
  67 |       await loginPassword.fill('MapleTest123!');
  68 |       await pause(page, 900);
  69 |     }
  70 |     if (await loginSubmit.isVisible()) {
  71 |       await loginSubmit.click();
  72 |       await pause(page, 2200);
  73 |     }
  74 |   }
  75 | 
  76 |   await page.goto('/app/onboarding', { waitUntil: 'domcontentloaded' });
  77 |   await pause(page, 2400);
  78 | 
  79 |   await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  80 |   await pause(page, 2200);
  81 | 
  82 |   await page.goto('/app/jobs', { waitUntil: 'domcontentloaded' });
  83 |   await pause(page, 2200);
  84 | 
  85 |   await expect(page).toHaveURL(/\/app\/jobs|\/login/);
  86 | });
  87 | 
```