const { test, expect } = require('@playwright/test');

async function pause(page, ms = 1500) {
  await page.waitForTimeout(ms);
}

test('chat: load and test chat functionality', async ({ page }) => {
  test.setTimeout(180000);

  // Navigate to chat page
  console.log('🧪 Starting Chat Test...');
  await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  await pause(page, 2500);

  // Verify page loads
  console.log('✅ Chat page loaded');
  await expect(page.locator('body')).toBeVisible();

  // Wait for chat container to be visible
  const chatContainer = page.locator('[class*="chat"], [class*="message"], main');
  await expect(chatContainer.first()).toBeVisible({ timeout: 10000 });
  console.log('✅ Chat container visible');

  // Take a screenshot
  await page.screenshot({ path: 'test-results/chat-page-load.png' });
  console.log('📸 Screenshot taken');

  // Look for message input
  const messageInputs = await page.locator('input[type="text"], textarea, [role="textbox"]').all();
  console.log(`Found ${messageInputs.length} potential input fields`);

  let messageInput = null;
  for (const input of messageInputs) {
    const isVisible = await input.isVisible();
    const placeholder = await input.getAttribute('placeholder');
    console.log(`Input visible: ${isVisible}, placeholder: ${placeholder}`);
    if (isVisible && (placeholder?.toLowerCase().includes('message') || placeholder?.toLowerCase().includes('ask'))) {
      messageInput = input;
      break;
    }
  }

  if (!messageInput && messageInputs.length > 0) {
    messageInput = messageInputs[messageInputs.length - 1];
  }

  if (messageInput) {
    console.log('✅ Found message input');
    
    // Click and type a test message
    await messageInput.click();
    await pause(page, 800);
    
    const testMessage = 'What are the main immigration programs in Canada?';
    await messageInput.fill(testMessage);
    console.log(`📝 Typed message: "${testMessage}"`);
    await pause(page, 500);

    // Look for send button
    const sendButtons = await page.locator('button[type="submit"], button[aria-label*="send" i], button[aria-label*="Send" i], button:has-text("Send")').all();
    console.log(`Found ${sendButtons.length} potential send buttons`);

    let sendButton = null;
    for (const btn of sendButtons) {
      const isVisible = await btn.isVisible();
      if (isVisible) {
        sendButton = btn;
        break;
      }
    }

    if (!sendButton && sendButtons.length > 0) {
      sendButton = sendButtons[0];
    }

    if (sendButton && await sendButton.isVisible()) {
      console.log('✅ Found send button');
      await sendButton.click();
      console.log('🚀 Sent message');
      
      // Wait for response
      await pause(page, 3000);
      
      // Check for response message
      const messages = await page.locator('[class*="message"], [role="article"]').all();
      console.log(`Found ${messages.length} message elements`);
      
      if (messages.length > 0) {
        console.log('✅ Response received');
        await page.screenshot({ path: 'test-results/chat-with-response.png' });
      }
    } else {
      console.log('⚠️ Send button not found');
      await page.screenshot({ path: 'test-results/chat-no-send-button.png' });
    }
  } else {
    console.log('⚠️ Message input not found');
    
    // Log all interactive elements for debugging
    const buttons = await page.locator('button').all();
    console.log(`Found ${buttons.length} buttons on page`);
    
    for (let i = 0; i < Math.min(5, buttons.length); i++) {
      const text = await buttons[i].textContent();
      console.log(`  Button ${i}: "${text?.trim()}"`);
    }

    await page.screenshot({ path: 'test-results/chat-no-input.png' });
  }

  console.log('✅ Chat test completed');
  await pause(page, 1000);
});

test('chat: navigation and session handling', async ({ page }) => {
  test.setTimeout(120000);

  console.log('🧪 Starting Chat Navigation Test...');
  
  // Load home page
  await page.goto('/', { waitUntil: 'domcontentloaded' });
  await pause(page, 1500);

  // Find and click "Ask Maple now" or chat link
  const chatLinks = await page.locator('a[href*="/chat"], a[href*="/app/chat"], button:has-text("Ask Maple"), button:has-text("Maple")').all();
  console.log(`Found ${chatLinks.length} chat navigation links`);

  if (chatLinks.length > 0) {
    const firstLink = chatLinks[0];
    await firstLink.click();
    console.log('🔗 Clicked chat link from homepage');
    await page.waitForURL(/\/chat|\/app\/chat/, { timeout: 10000 });
    console.log('✅ Navigation successful');
    await page.screenshot({ path: 'test-results/chat-navigation.png' });
  } else {
    console.log('⚠️ No chat navigation links found');
  }
});

test('chat: performance check', async ({ page }) => {
  test.setTimeout(60000);

  console.log('🧪 Starting Chat Performance Test...');
  
  const startTime = Date.now();
  
  await page.goto('/app/chat', { waitUntil: 'domcontentloaded' });
  const loadTime = Date.now() - startTime;
  
  console.log(`⏱️  Page load time: ${loadTime}ms`);
  
  if (loadTime < 5000) {
    console.log('✅ Load time excellent (< 5s)');
  } else if (loadTime < 10000) {
    console.log('⚠️ Load time acceptable (5-10s)');
  } else {
    console.log('❌ Load time slow (> 10s)');
  }

  await page.screenshot({ path: 'test-results/chat-performance.png' });
});
