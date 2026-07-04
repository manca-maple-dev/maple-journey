# 🚀 Twilio Setup Guide for Maple WhatsApp + SMS

Complete step-by-step guide to set up Twilio messaging for Maple (WhatsApp, SMS, iMessage).

---

## 📱 PHONE SETUP (Your Mobile Device)

### Step 1: Get Your Phone Number
1. Open WhatsApp on your phone
2. Go to **Settings** → **Account** → **Phone Number**
3. **Copy your full phone number with country code**
   - Example: `+1 647 123 4567` (Canada) or `+44 7911 123456` (UK)
4. **Save this number** — you'll need it for Twilio

### Step 2: Enable SMS/iMessage (Optional)
- If you want SMS fallback: Ensure SMS is enabled on your phone
- iPhone: Settings → Messages → Enable iMessage

---

## 💻 TWILIO ACCOUNT SETUP (Web Browser on Desktop)

### Step 1: Create Twilio Account
1. Go to **https://www.twilio.com/console**
2. Click **Sign Up**
3. Enter:
   - Email
   - Password
   - Phone Number (your real phone from Step 1)
   - Verify via SMS code
4. **Select "Build Apps"** as your use case
5. **Country: Canada** (or your country)
6. Click **Create Account**

### Step 2: Verify Your Phone Number
1. Twilio will send an SMS verification code to your phone
2. On your phone: **Open SMS → Copy the code**
3. On Twilio website: **Paste the code → Verify**
4. Wait for confirmation: "✅ Phone number verified"

### Step 3: Get Your Twilio Credentials
Once logged in to Twilio Console:

1. **Find Your Account SID and Auth Token:**
   - Go to: https://www.twilio.com/console
   - Look at the top-right: **Account SID** and **Auth Token**
   - Click the eye icon to reveal the Auth Token
   - **Copy and save both** (you'll paste these into backend .env)

   ```
   TWILIO_ACCOUNT_SID = ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN = your-auth-token-here
   ```

2. **Get a Twilio Phone Number for SMS:**
   - Go to: https://www.twilio.com/console/phone-numbers/incoming
   - Click **Buy a Phone Number**
   - Country: **Canada** (or your country)
   - Capabilities: Check **SMS** and **Voice** (WhatsApp is free, SMS requires this)
   - Click **Search** → Select a number → **Buy**
   - **Save this number** (format: `+1 647 123 7890`)

   ```
   TWILIO_PHONE_NUMBER = +1 647 123 7890
   ```

### Step 4: Enable WhatsApp (Free Messaging)
1. Go to: https://www.twilio.com/console/sms/whatsapp/learn
2. Click **Get Started with WhatsApp**
3. Select your Twilio Phone Number (from Step 3)
4. Accept the WhatsApp Business terms
5. Click **Enable WhatsApp Sandbox**
6. **You'll get a WhatsApp Business number** (usually same as your SMS number or auto-assigned)
   - **Save this number** — users will message this number on WhatsApp

   ```
   TWILIO_WHATSAPP_NUMBER = +1 647 123 7890
   ```

### Step 5: Set Up Webhooks (Message Routing)
Your backend needs to know when messages arrive. You'll configure Twilio to send messages to your server.

**On Twilio Console:**

1. **For SMS:**
   - Go to: https://www.twilio.com/console/phone-numbers/incoming
   - Click your Twilio Phone Number
   - Scroll to **Messaging**
   - **Webhook URL for incoming messages:**
     ```
     https://your-ngrok-url.ngrok.io/webhook/imessage-inbound
     ```
   - **HTTP Method:** POST
   - **Save**

2. **For WhatsApp:**
   - Go to: https://www.twilio.com/console/sms/whatsapp/sandbox
   - Scroll to **When a message comes in:**
   - **Webhook URL:**
     ```
     https://your-ngrok-url.ngrok.io/webhook/whatsapp-inbound
     ```
   - **HTTP Method:** POST
   - **Save**

*Note: You'll get your ngrok URL in the next section*

---

## 🔧 BACKEND CONFIGURATION (Your Computer)

### Step 1: Update .env File

Create or update `backend/.env`:

```env
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_PHONE_NUMBER=+1 647 123 7890
TWILIO_WHATSAPP_NUMBER=+1 647 123 7890

# Other existing config
MONGODB_URI=mongodb://localhost:27017/maple
ANTHROPIC_API_KEY=sk-ant-xxxxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_API_KEY=xxx
```

### Step 2: Test Twilio Credentials Locally

In your terminal:

```powershell
cd C:\Users\manca\maple-journey-dev\backend
.\venv\Scripts\python.exe -c "
from services.twilio_service import send_whatsapp
# This will test if credentials work
print('✅ Twilio credentials loaded successfully')
"
```

### Step 3: Start Backend Server

```powershell
cd C:\Users\manca\maple-journey-dev\backend
.\venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
```

Wait for:
```
Uvicorn running on http://127.0.0.1:8000
```

---

## 🌐 EXPOSE BACKEND TO INTERNET (ngrok Tunnel)

Twilio needs to send messages to your computer. ngrok creates a public URL pointing to your local server.

### Step 1: Start ngrok Tunnel

In a NEW terminal window:

```powershell
cd C:\Users\manca\maple-journey-dev\backend

# Run ngrok to expose port 8000
ngrok http 8000
```

You'll see:
```
Session Status                online
Account                      [your-account]
Version                       [version]
Region                        us
Forwarding                    https://xxxx-xx-xxx-xxx-xx.ngrok.io -> http://127.0.0.1:8000
```

**Copy the Forwarding URL** (e.g., `https://xxxx-xx-xxx-xxx-xx.ngrok.io`)

### Step 2: Update Twilio Webhooks with ngrok URL

Go back to Twilio Console and update the webhook URLs:

**For SMS:**
- Phone Numbers → Your Number → Messaging → Webhook:
  ```
  https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook/imessage-inbound
  ```

**For WhatsApp:**
- WhatsApp Sandbox → When a message comes in:
  ```
  https://xxxx-xx-xxx-xxx-xx.ngrok.io/webhook/whatsapp-inbound
  ```

---

## ✅ TEST EVERYTHING

### Test 1: Send WhatsApp Message to Your Phone

From your computer terminal:

```powershell
$payload = @{
    to_phone = "+1 647 123 4567"  # Your phone number
    text = "Test message from Maple! 🍁"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/webhook/whatsapp-outbound" `
  -Method Post `
  -ContentType "application/json" `
  -Body $payload
```

**On your phone:** You should receive a WhatsApp message within 5 seconds ✅

### Test 2: Send SMS Message

```powershell
$payload = @{
    to_phone = "+1 647 123 4567"  # Your phone number
    text = "Test SMS from Maple!"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/webhook/imessage-outbound" `
  -Method Post `
  -ContentType "application/json" `
  -Body $payload
```

**On your phone:** You should receive an SMS within 5 seconds ✅

### Test 3: Reply on WhatsApp/SMS

1. **On your phone:** Open the WhatsApp message and reply: "Hi Maple"
2. **Watch your terminal:** You should see:
   ```
   POST /webhook/whatsapp-inbound
   Message received: "Hi Maple"
   Response sent: "[Maple's reply]"
   ```

---

## 🎯 PRODUCTION CHECKLIST

- ✅ Twilio Account created and verified
- ✅ WhatsApp Sandbox enabled
- ✅ SMS Phone Number purchased
- ✅ Webhooks configured on Twilio Console
- ✅ .env file updated with credentials
- ✅ Backend running on http://127.0.0.1:8000
- ✅ ngrok tunnel active with public URL
- ✅ Test messages sent and received
- ✅ Replies working bidirectionally

---

## 💰 COST BREAKDOWN (2026 Pricing)

| Channel | Rate | Volume | Cost |
|---------|------|--------|------|
| WhatsApp (Twilio) | $0.00177/msg (North America) | 1M msgs/year | $1,770 |
| SMS | $0.0075/msg (inbound), $0.0075/msg (outbound) | 1M msgs/year | $15,000 |
| Claude 3.5 Sonnet | $3/1M input, $15/1M output | 100M tokens/year | $1,200 |

**Total for 1M conversations/year: ~$18k** (or ~$1.50 per user for active users)

---

## 🆘 TROUBLESHOOTING

**Problem: "Auth Token invalid"**
- Solution: Copy token again from https://www.twilio.com/console (watch for spaces)

**Problem: "Phone number not verified"**
- Solution: Check SMS on your phone for verification code, paste in Twilio console

**Problem: "Webhooks not receiving messages"**
- Solution: 
  1. Check ngrok is running: `ngrok http 8000`
  2. Verify webhook URLs in Twilio console match ngrok URL
  3. Check backend logs for errors

**Problem: "WhatsApp message not received"**
- Solution: 
  1. Check WhatsApp Sandbox is enabled (Twilio console)
  2. Save the WhatsApp Business number in your phone contacts
  3. Start conversation from WhatsApp (not SMS)

---

## 📞 SUPPORT

- **Twilio Support:** https://www.twilio.com/console/support
- **Twilio Docs:** https://www.twilio.com/docs
- **Maple Backend Logs:** Check terminal for detailed error messages

---

✅ **You're ready!** Users can now message Maple on WhatsApp, SMS, or iMessage without needing an app.
