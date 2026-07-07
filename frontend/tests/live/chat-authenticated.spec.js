const { test, expect } = require('@playwright/test');

async function pause(page, ms = 1500) {
  await page.waitForTimeout(ms);
}

async function acceptCookies(page) {
  try {
    const acceptBtn = page.locator('button:has-text("Accept all cookies"), button:has-text("Accept")').first();
    if (await acceptBtn.isVisible({ timeout: 3000 })) {
      await acceptBtn.click();
      console.log('🍪 Cookies accepted');
      await pause(page, 500);
    }
  } catch (e) {
    console.log('⚠️ No cookie banner found');
  }
}

test('chat: authenticated chat interaction', async ({ page }) => {
  test.setTimeout(180000);

  console.log('🧪 Starting Authenticated Chat Test...');
  
  // Go to homepage
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await pause(page, 1500);
  await acceptCookies(page);

  // Look for chat button or link
  const askMapleBtn = page.locator('button:has-text("Ask Maple"), a:has-text("Ask Maple"), button:has-text("Start your journey")').first();
  
  if (await askMapleBtn.isVisible()) {
    console.log('✅ Found "Ask Maple" button');
    await askMapleBtn.click();
    await pause(page, 2000);
  }

  // Navigate to chat directly
  console.log('🔄 Navigating to chat page...');
  await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  await pause(page, 2000);

  // Screenshot page state
  await page.screenshot({ path: 'test-results/chat-auth-check.png' });

  // Check if on login page
  const loginForm = page.locator('[class*="login"], [class*="signin"], form:has-text("Sign in")').first();
  const isLoginPage = await loginForm.isVisible({ timeout: 2000 }).catch(() => false);

  if (isLoginPage) {
    console.log('🔐 Login page detected - attempting demo access');
    
    // Try demo email/password
    const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    const loginBtn = page.locator('button:has-text("Sign in"), button[type="submit"]').first();

    if (await emailInput.isVisible() && await passwordInput.isVisible()) {
      console.log('📝 Attempting demo login...');
      
      await emailInput.fill('demo@maplejourney.ca');
      await pause(page, 500);
      await passwordInput.fill('demo123');
      await pause(page, 500);
      
      if (await loginBtn.isVisible()) {
        await loginBtn.click();
        await pause(page, 3000);
        console.log('🔑 Login attempted');
      }
    }
  }

  // Check for chat interface
  const chatInputs = await page.locator('input[type="text"], textarea, [role="textbox"]').all();
  console.log(`📋 Found ${chatInputs.length} input fields`);

  if (chatInputs.length > 0) {
    const visibleInputs = [];
    for (const input of chatInputs) {
      if (await input.isVisible()) {
        visibleInputs.push(input);
      }
    }

    console.log(`✅ Found ${visibleInputs.length} visible input fields`);

    if (visibleInputs.length > 0) {
      const messageInput = visibleInputs[visibleInputs.length - 1];
      
      // Type message
      const testMessage = 'Can you help me understand PR requirements?';
      await messageInput.click();
      await pause(page, 500);
      await messageInput.type(testMessage, { delay: 30 });
      console.log(`📝 Typed: "${testMessage}"`);
      
      await pause(page, 500);

      // Send message
      const sendBtn = page.locator('button[aria-label*="send" i], button[type="submit"]:near(input[type="text"]), button:has-text("Send")').first();
      if (await sendBtn.isVisible()) {
        await sendBtn.click();
        console.log('🚀 Message sent');
        
        // Wait for response
        await pause(page, 4000);
        
        // Check for response message
        const messages = await page.locator('[class*="message"], [role="article"], [class*="chat"]').all();
        console.log(`✅ Found ${messages.length} message elements`);
        
        await page.screenshot({ path: 'test-results/chat-with-response.png' });
      } else {
        console.log('⚠️ Send button not found');
        await page.screenshot({ path: 'test-results/chat-no-send-btn.png' });
      }
    }
  } else {
    console.log('⚠️ No input fields found on page');
    
    // List all visible text on page for debugging
    const bodyText = await page.textContent('body');
    const preview = bodyText?.substring(0, 200) || 'N/A';
    console.log(`Page text preview: ${preview}...`);
    
    await page.screenshot({ path: 'test-results/chat-no-inputs.png' });
  }
});

test('chat: page load and ui structure', async ({ page }) => {
  test.setTimeout(60000);

  console.log('🧪 Starting Chat UI Structure Test...');
  
  // Load chat page
  await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  await pause(page, 2000);
  
  // Verify essential elements
  const mainContent = page.locator('main, [class*="app"], [class*="layout"]').first();
  await expect(mainContent).toBeVisible({ timeout: 10000 });
  console.log('✅ Main content visible');

  // Check for header/navigation
  const header = page.locator('header, nav, [class*="header"], [class*="nav"]').first();
  const hasHeader = await header.isVisible({ timeout: 5000 }).catch(() => false);
  console.log(`${hasHeader ? '✅' : '⚠️'} Header visible: ${hasHeader}`);

  // Check for sidebar or menu
  const sidebar = page.locator('[class*="sidebar"], [class*="menu"], aside').first();
  const hasSidebar = await sidebar.isVisible({ timeout: 5000 }).catch(() => false);
  console.log(`${hasSidebar ? '✅' : '⚠️'} Sidebar visible: ${hasSidebar}`);

  // Check for any form elements
  const forms = await page.locator('form, [role="form"]').all();
  console.log(`ℹ️  Found ${forms.length} form elements`);

  // Log button count
  const buttons = await page.locator('button').all();
  console.log(`ℹ️  Found ${buttons.length} buttons`);

  // Verify page title
  const title = await page.title();
  console.log(`📄 Page title: "${title}"`);
  expect(title.toLowerCase()).toContain('maple');

  await page.screenshot({ path: 'test-results/chat-ui-structure.png' });
  console.log('✅ UI Structure test completed');
});

test('chat: api connectivity check', async ({ page }) => {
  test.setTimeout(60000);

  console.log('🧪 Starting API Connectivity Test...');
  
  // Intercept API calls
  let apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('api') || request.url().includes('maplejourney.ca')) {
      apiCalls.push({
        url: request.url(),
        method: request.method(),
        time: new Date().toLocaleTimeString()
      });
      console.log(`📡 API Call: ${request.method()} ${request.url()}`);
    }
  });

  // Load chat
  await page.goto('/app/chat', { waitUntil: 'networkidle' });
  await pause(page, 2000);

  console.log(`📊 Total API calls: ${apiCalls.length}`);
  
  // Check for backend URL in environment
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  console.log(`🔌 Backend URL: ${backendUrl}`);

  if (apiCalls.length > 0) {
    console.log('✅ API endpoints are being called');
    
    // Check for specific endpoints
    const hasAuthApi = apiCalls.some(c => c.url.includes('/auth'));
    const hasChatApi = apiCalls.some(c => c.url.includes('/chat') || c.url.includes('/message'));
    
    console.log(`${hasAuthApi ? '✅' : '⚠️'} Auth API: ${hasAuthApi}`);
    console.log(`${hasChatApi ? '✅' : '⚠️'} Chat API: ${hasChatApi}`);
  } else {
    console.log('⚠️ No API calls detected');
  }

  await page.screenshot({ path: 'test-results/chat-api-check.png' });
});
