# Quick Setup: Link Bot Token to Railway

## Step 1: Create Your Bot Token (5 minutes)

```
1. Open Telegram app
2. Search for: @BotFather
3. Send: /newbot
4. Name your bot: MapleJourney Collector Bot
5. Username: maplejourney_collector_bot
   
⚠️  USERNAME MUST BE UNIQUE GLOBALLY
    (If not available, add date: maplejourney_collector_bot_2024)

✅ BotFather returns:
   "Done! Congratulations on your new bot. You will find it at 
    t.me/maplejourney_collector_bot. You can now add a description..."
    
   "Use this token to access the HTTP API:
    123456789:ABCdefGHIjklmnoPQRstuvWXyz-keep-this-secret"
```

---

## Step 2: Add Token to Railway (2 minutes)

**A. Navigate to Railway**
```
1. Go to: https://railway.com
2. Click your project: "MapleJourney"
3. Select "MapleJourney" service
4. Click "Variables" tab
```

**B. Add Environment Variable**
```
Click "+ New Variable"

Variable Name:    TELEGRAM_BOT_TOKEN
Variable Value:   123456789:ABCdefGHIjklmnoPQRstuvWXyz
                  (paste the token from BotFather)

Click "Add"
```

You should see:
```
TELEGRAM_BOT_TOKEN = 123456789:ABCdefGHIjklmnoPQRstuvWXyz
MONGO_URL = mongodb+srv://...
DB_NAME = maplejourney
... (other variables)
```

**C. Deploy**
```
Go to "Build & Deploy" tab
Wait for auto-redeploy (~2 minutes)
```

---

## Step 3: Verify Backend is Running

Check logs:
```
Click "Logs" tab in Railway

You should see:
✅ Telegram bot initialized and polling started
✅ Telegram monitoring service started (60-second intervals)
```

---

## Step 4: Test the Bot (1 minute)

**In Your Telegram App:**
```
1. Search: @maplejourney_collector_bot
2. Send: /start
   
   Bot responds:
   "Welcome to MapleJourney Data Collector 🚀
    
    I help collect your information for government benefits.
    
    Commands:
    /collect - Start collecting your information
    /status - Check your last submission
    /cancel - Cancel current operation"

3. Send: /collect
   
   Bot responds:
   "Select a form to fill out:
   📝 Quick Profile
   🏠 Housing Assistance
   💼 Job Search
   📚 Education"

4. Click "Quick Profile"
   
   Bot responds:
   "Let's collect your information.
    
    First, your email address:
    (This helps us contact you with your results)"

5. Send: john@example.com
   
   Bot responds:
   "✅ Email saved!
    
    Now, your phone number:
    (Format: +1-XXX-XXX-XXXX or 1-XXX-XXX-XXXX)"

6. Continue filling out all fields...
```

---

## Step 5: Verify Data is Saving

Check your API:
```
1. Open: https://web-production-1acc6.up.railway.app/docs
2. Scroll to: /api/telegram/status
3. Click "Try it out"
4. Click "Execute"

Response:
{
  "total_records": 1,
  "completed": 1,
  "today": 1,
  "by_form_type": {
    "profile": 1
  }
}
```

---

## Step 6: View on Dashboard

1. Go to: https://web-production-1acc6.up.railway.app/admin
2. Click "Telegram" or find "Data Collection"
3. You should see real-time metrics:
   - Collections Today: 1
   - Active Sessions: 0
   - Avg Completion Time: 45 seconds
   - Form Distribution chart

---

## ✅ Success Indicators

- [ ] Bot responds to `/start`
- [ ] `/collect` shows form options
- [ ] Can fill out and submit form
- [ ] `/api/telegram/status` shows records
- [ ] Dashboard shows metrics
- [ ] Data visible in MongoDB

---

## If Bot Doesn't Respond

**Check 1: Railway Logs**
```
Railway > MapleJourney > Logs

Look for:
❌ "TELEGRAM_BOT_TOKEN not configured"
   → Add token and redeploy

❌ "Failed to initialize Telegram bot: ..."
   → Token is invalid or wrong format
   → Copy from BotFather again
```

**Check 2: Token Format**
```
Correct: 123456789:ABCdefGHIjklmnoPQRstuvWXyz
         (9 digits : 35 characters)

Wrong: Just the username
Wrong: With quotes like "123456789:..."
Wrong: Incomplete token
```

**Check 3: Redeploy**
```
After adding token:
1. Go to Railway > Build & Deploy
2. Wait for rebuild
3. Check status light turns green
4. Check logs for startup messages
```

---

## Now What?

Your data collection pipeline is LIVE:

✅ Users in Telegram sending data
✅ Data stored in MongoDB
✅ Real-time monitoring active
✅ Admin dashboard showing metrics
✅ APIs ready for integration
✅ CSV export available

Next steps:
1. Promote bot to users
2. Monitor metrics dashboard
3. Export data for analysis
4. Connect to benefits matching
5. Scale as needed

---

## Bot Commands Reference

User can send these to the bot:

```
/start          - Start fresh conversation
/collect        - Begin data collection
/status         - See last submission
/cancel         - Stop current operation
```

You (admin) can also:

```
/api/telegram/status           - See all submissions
/api/telegram/export           - Download as CSV
/api/telegram/monitor/         - See alerts & metrics
/api/telegram/data/{user_id}  - Check specific user
```

---

## FAQ

**Q: Where does the data go?**
A: MongoDB database. Encrypted at rest. Only admin can access via API.

**Q: How long does data stay?**
A: Forever (or until you delete). Can implement auto-archival for old data.

**Q: Can I edit collected data?**
A: Yes, via `/api/telegram/data/{id}` endpoint (admin only).

**Q: Can I delete data?**
A: Yes, via `/api/telegram/data/{id}` DELETE endpoint (admin only).

**Q: How do I export data?**
A: POST to `/api/telegram/export` with date range and form types.

**Q: Can users collect multiple forms?**
A: Yes! Same user can submit Profile, Housing, Jobs, Education separately.

**Q: How do I know if user is real?**
A: Check `/api/telegram/data/{user_id}/verify` endpoint to mark verified.

**Q: Can I integrate with WhatsApp?**
A: Yes! Phase 2 plan is to add Twilio WhatsApp integration.

---

**🎉 You're now collecting professional structured data directly in Telegram!**
