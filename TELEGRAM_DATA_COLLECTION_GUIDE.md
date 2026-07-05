# Professional Telegram Data Collection Pipeline
## Building a Scalable, Real-Time Data Collection System

This guide walks you through setting up a professional-grade Telegram bot for structured data collection with MongoDB integration.

---

## 🎯 Overview

### What We Built
A **production-ready Telegram data collection system** that:
- ✅ Collects structured user data (email, phone, address, income, etc.)
- ✅ Validates all inputs in real-time
- ✅ Stores data securely in MongoDB
- ✅ Provides real-time monitoring & analytics
- ✅ Exports data as CSV for analysis
- ✅ Scales to millions of users
- ✅ Zero confusion - organized forms, not scattered emails/texts

### Forms Available
1. **Quick Profile** - Basic user information
2. **Housing Assistance** - Specialized for housing benefits
3. **Job Search** - Employment-focused data
4. **Education** - Educational background

---

## 🚀 Quick Start

### Step 1: Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow prompts:
   - Name: "MapleJourney Collector" (or custom name)
   - Username: "maplejourney_collector_bot" (must be unique)
4. **Save the token** (looks like: `123456789:ABCdefGHIjklmnoPQRstuvWXyz`)

### Step 2: Set Environment Variables

Add to your `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN="YOUR_TOKEN_HERE"
TELEGRAM_WEBHOOK_URL="https://your-domain.com/api/telegram/webhook"
TELEGRAM_ADMIN_CHAT_ID="your_telegram_user_id"  # Get from @userinfobot

# MongoDB Collections (auto-created)
TELEGRAM_COLLECTION_FORMS="telegram_collection_forms"
TELEGRAM_COLLECTED_DATA="telegram_collected_data"
TELEGRAM_USER_SESSIONS="telegram_user_sessions"
```

### Step 3: Get Your Telegram User ID

1. Open Telegram
2. Search for **@userinfobot**
3. Send `/start`
4. Copy your User ID (e.g., `1234567890`)

---

## 🔧 Integration into FastAPI

### Add to `backend/server.py`

```python
# At the top of imports
from routers import telegram
from services.telegram_collector import TelegramDataCollector
import os

# In your FastAPI setup section:
# Include Telegram router
app.include_router(telegram.router)

# Initialize Telegram bot (after creating app)
@app.on_event("startup")
async def startup_telegram():
    """Initialize Telegram bot on server startup"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        telegram.telegram_collector.bot_token = token
        app.telegram_app = await telegram.telegram_collector.initialize_app()
        logger.info("✅ Telegram bot initialized")
```

### Update `backend/requirements.txt`

```
python-telegram-bot==20.3
```

Install:
```bash
pip install python-telegram-bot==20.3
```

---

## 📊 API Endpoints

### 1. Get Collection Status
```bash
GET /api/telegram/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_records": 1500,
  "completed": 1495,
  "today": 145,
  "by_form_type": {
    "profile": 800,
    "housing": 450,
    "jobs": 200,
    "education": 45
  },
  "collected_at": "2026-07-05T15:30:00"
}
```

### 2. Get Real-Time Metrics
```bash
GET /api/telegram/metrics
Authorization: Bearer {token}
```

**Response:**
```json
{
  "active_sessions": 23,
  "completed_today": 145,
  "avg_completion_time_seconds": 245.5,
  "forms_by_type": {
    "profile": 800,
    "housing": 450,
    "jobs": 200,
    "education": 45
  },
  "top_fields": {
    "email": 1495,
    "phone": 1495,
    "address": 1487,
    "immigration_status": 1495,
    "annual_income": 1482
  },
  "hourly_breakdown": {
    "00:00": 5,
    "08:00": 25,
    "09:00": 38,
    "10:00": 42,
    "11:00": 35
  }
}
```

### 3. Export Data as CSV
```bash
POST /api/telegram/export
Authorization: Bearer {token}
Content-Type: application/json

{
  "start_date": "2026-07-01T00:00:00",
  "end_date": "2026-07-05T23:59:59",
  "form_type": "profile",
  "limit": 1000
}
```

### 4. Get User's Collected Data
```bash
GET /api/telegram/data/{user_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "64a1b2c3d4e5f6g7h8i9j0k1",
  "user_id": 1234567890,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "collected_data": {
    "email": "john.doe@example.com",
    "phone": "+1-647-555-0100",
    "address": "123 Main St, Toronto, ON M5V 3A8",
    "full_name": "John Doe",
    "immigration_status": "Permanent Resident",
    "annual_income": 65000,
    "dependent_children": 2
  },
  "form_type": "profile",
  "collected_at": "2026-07-05T14:22:30",
  "status": "completed"
}
```

### 5. Get Collection Dashboard
```bash
GET /api/telegram/dashboard
Authorization: Bearer {token}
```

---

## 🤖 Telegram Bot Commands

Users interact with the bot directly in Telegram:

### Available Commands
- **/start** - Welcome message with instructions
- **/collect** - Begin data collection form
- **/status** - Check your submitted data
- **/cancel** - Cancel current operation

### Data Collection Flow

**User Types:** `/collect`

**Bot Shows:**
```
📋 Select the form you'd like to complete:
[📝 Quick Profile]  [🏠 Housing Assistance]
[💼 Job Search]     [📚 Education]
[❌ Cancel]
```

**Then Collects (One at a time):**
1. 📧 Email - with validation
2. 📱 Phone - with format validation
3. 🏘️ Address - minimum length check
4. 👤 Full Name - validation
5. 🛂 Immigration Status - dropdown
6. 💰 Annual Income - number validation
7. 👨‍👩‍👧‍👦 Dependent Children - number validation
8. ✅ Confirmation - review & submit

---

## 🔐 Data Validation

### Email Validation
- Pattern: `name@domain.com`
- Supports: `+` signs, dots, underscores, hyphens

### Phone Validation
- Formats accepted:
  - `+1-647-555-0100`
  - `6475550100`
  - `647-555-0100`
  - `(647) 555-0100`

### Address Validation
- Minimum 10 characters
- Supports: street, city, province, postal code, country

### Income Validation
- Must be number
- No negative values
- Supports: `35000` or `35,000` (with comma)

### Children Validation
- Integer 0-20
- No decimals

---

## 📈 Real-Time Monitoring

### Dashboard Features
1. **Live Stats**
   - Total records collected
   - Completed submissions
   - Today's count
   - Breakdown by form type

2. **Performance Metrics**
   - Active sessions (last 24h)
   - Average completion time
   - Top collected fields
   - Hourly breakdown

3. **Data Export**
   - CSV export with date filters
   - Form type filtering
   - Admin-only access

---

## 🛡️ Security & Privacy

### Data Protection
- ✅ All data encrypted at rest (MongoDB encryption)
- ✅ HTTPS-only communication
- ✅ JWT authentication for API access
- ✅ Admin-only access to sensitive endpoints
- ✅ User data isolation (users see only own data)

### Admin Verification
Mark data as verified once reviewed:
```bash
POST /api/telegram/data/{user_id}/verify
Authorization: Bearer {admin_token}
```

---

## 🚢 Deployment on Railway

### Step 1: Update Requirements
```bash
cd backend
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add: Telegram bot dependencies"
```

### Step 2: Push to Production
```bash
git push origin main
```

Railway auto-detects changes and redeployment.

### Step 3: Add Environment Variables in Railway Dashboard

Go to: Railway Dashboard → MapleJourney Service → Variables

Add:
```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ADMIN_CHAT_ID=your_user_id
```

### Step 4: Verify Deployment
```bash
railway logs --service MapleJourney --tail 50
```

Look for: `✅ Telegram bot initialized`

---

## 📱 User Experience Flow

### First-Time User
```
User: /start
Bot: Welcome message + commands

User: /collect
Bot: Form selection (profile/housing/jobs/education)

User: Clicks "📝 Quick Profile"
Bot: Email field

User: john@example.com
Bot: ✅ Valid. Next field...

[Continues through all 7 fields with validation]

User: Sees confirmation
Bot: All data correct?
User: Clicks ✅ Confirm

Bot: 🎉 Data submitted! Record ID: 64a1b2c3d4e5...
```

---

## 🔄 Integration with Benefits Matching

### Automatic Pipeline
1. **Data Collected** via Telegram
   ↓
2. **Verified** by admin
   ↓
3. **Matched** against benefits database (`/api/benefits/my-benefits`)
   ↓
4. **Recommendations** sent via email + Telegram notification
   ↓
5. **User tracks** application status (`/api/benefits/track-application`)

---

## 📊 Analytics & Reporting

### Get Collection History
```bash
GET /api/telegram/users/{user_id}/history?limit=10
Authorization: Bearer {token}
```

### Export by Date Range
```bash
POST /api/telegram/export
{
  "start_date": "2026-07-01T00:00:00",
  "end_date": "2026-07-05T23:59:59",
  "limit": 5000
}
```

Returns CSV with all fields.

---

## 🎯 Next Steps for Scaling

### Phase 1 (Current)
- ✅ Single Telegram bot
- ✅ 7 data fields
- ✅ 4 form types
- ✅ Real-time validation

### Phase 2 (Coming)
- 📱 Multi-language support (French, Spanish, Chinese)
- 🤖 AI-powered eligibility pre-screening
- 📧 Automatic email confirmation
- 💬 WhatsApp integration

### Phase 3 (Future)
- 🌍 International expansion (UK, Australia, USA)
- 🔗 Direct government API integration
- 📊 Advanced analytics dashboard
- 🚀 Webhooks for third-party integrations

---

## 🐛 Troubleshooting

### Bot Not Responding
**Check:**
1. Token is correct: `echo $TELEGRAM_BOT_TOKEN`
2. Server is running: `railway logs`
3. Firewall allows Telegram: usually open

**Fix:**
```bash
# Restart the bot
railway redeploy --service MapleJourney
```

### Data Not Saving
**Check:**
1. MongoDB connection: `MONGODB_URI` in env
2. Collections exist: Check MongoDB Atlas
3. Permissions: User has write access

**Fix:**
```bash
# Check MongoDB
mongo "mongodb+srv://user:pass@cluster.mongodb.net/maplejourney"
> db.telegram_collected_data.find({}).limit(1)
```

### High Response Time
**Optimize:**
1. Add database indexes
2. Implement caching
3. Scale MongoDB resources

---

## 📞 Support

**Questions or Issues?**
1. Check Railway logs: `railway logs`
2. Test API: POST to `/api/telegram/webhook`
3. Contact admin: Use `/api/telegram/dashboard`

---

## ✅ Checklist Before Going Live

- [ ] Telegram bot created with BotFather
- [ ] Bot token added to environment
- [ ] MongoDB collections verified
- [ ] API endpoints tested
- [ ] Admin user created
- [ ] Dashboard accessible
- [ ] Data export tested
- [ ] Email confirmations working
- [ ] Railway deployment stable
- [ ] Load testing completed
