# ✅ YOUR BOT CREDENTIALS READY

Your Telegram bot has been created! Here's what you need to do next:

## Your Credentials:

```
Bot Token:     8863872246:AAEOO3EdXk4KXRAwlVi03Gp1weILUfhuRN0
Admin Chat ID: 6351653716
```

---

## Add to Railway (Manual Steps - Web UI)

Since automated setup had issues, here are manual steps:

### Step 1: Go to Railway Variables

1. Open: https://railway.com
2. Click your project: **MapleJourney**
3. Select service: **web** (or the green service name)
4. Click tab: **Variables**

### Step 2: Add TELEGRAM_BOT_TOKEN

1. Click: **New Variable** button (top right)
2. Enter:
   - **Key:** `TELEGRAM_BOT_TOKEN`
   - **Value:** `8863872246:AAEOO3EdXk4KXRAwlVi03Gp1weILUfhuRN0`
3. Press: **Enter** or click **Add**

### Step 3: Add TELEGRAM_ADMIN_CHAT_ID

1. Click: **New Variable** button again
2. Enter:
   - **Key:** `TELEGRAM_ADMIN_CHAT_ID`
   - **Value:** `6351653716`
3. Press: **Enter** or click **Add**

### Step 4: Deploy

Railway auto-deploys when you add variables. Wait ~2 minutes for deployment to complete.

---

## Verify Deployment

Check logs to confirm bot initialized:

```
https://railway.com/project/4396a56b-ff26-4b1a-a645-017541463f36/service/10cf18fc-6d0c-490b-938b-cba7429fa133/logs?environmentId=f1cf66e3-ead7-4266-a6db-ed91e93a0f85
```

Look for message:
```
✅ Telegram bot initialized and polling started
✅ Telegram monitoring service started (60-second intervals)
```

---

## Test Your Bot

Once deployed:

1. Open Telegram app
2. Search: `@maplejourney_collector_bot`
3. Send: `/start`
4. Send: `/collect`
5. Fill out the form
6. Submit

---

## Success Indicators

After setup:
- ✅ Bot responds to `/start` in Telegram
- ✅ Data visible in `/api/telegram/status`
- ✅ Dashboard shows real-time metrics
- ✅ MongoDB has telegram_collected_data records

---

## If Something Goes Wrong

**Bot not responding?**
- Check Railway logs
- Verify token pasted correctly (no extra spaces)
- Wait 2-3 minutes for deployment

**Data not saving?**
- Check MongoDB connection
- Verify MONGO_URL in variables

**Need help?**
- See: QUICK_BOT_SETUP.md
- See: TELEGRAM_BOT_DATA_SCALING_GUIDE.md

---

## Keep These Credentials Safe!

⚠️ These tokens are production credentials:
- **Never share** the bot token
- **Never commit** to public repos
- **Keep in Railway environment** only
- **Use in backend/.env** locally only

---

## What's Running Now

✅ Backend integrated with bot
✅ Bot service ready to receive messages
✅ Monitoring service ready
✅ API endpoints ready
✅ Dashboard ready

**Just need to:** Add these 2 environment variables to Railway and deploy!

---

**Time to setup: 2 minutes**  
**Time to first data: 5 minutes**  
**Total: Less than 10 minutes**

Good luck! 🚀
