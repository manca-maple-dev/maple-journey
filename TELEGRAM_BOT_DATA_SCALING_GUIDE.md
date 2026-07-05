# Telegram Data Collection → Scaling Guide
**How to link your bot, collect data, and extract it as you grow**

---

## 🎯 ARCHITECTURE: How Data Flows

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEGRAM USER                           │
│  Types: /collect → Chooses Form → Fills 7 Fields → Confirms     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT SERVICE                          │
│   (backend/services/telegram_collector.py)                       │
│                                                                  │
│  ✅ Validates each field                                         │
│  ✅ Stores in-progress session state                            │
│  ✅ Manages 10-step conversation flow                           │
│  ✅ Handles user errors gracefully                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      MONGODB (THE VAULT)                         │
│                                                                  │
│  Collections:                                                    │
│  ├─ telegram_collected_data          ← User responses stored     │
│  │   Fields: email, phone, address, name, status, income, kids  │
│  │   _id: Auto-generated UUID per submission                    │
│  │   form_type: "profile" | "housing" | "jobs" | "education"   │
│  │   user_id: Telegram user ID                                  │
│  │   timestamp: When submitted                                  │
│  │                                                               │
│  ├─ telegram_user_sessions           ← Active chats             │
│  │   Tracks conversation state (which step user is on)          │
│  │                                                               │
│  ├─ telegram_metrics                 ← Real-time stats          │
│  │   Updated every 60 seconds                                   │
│  │   collections_today, active_sessions, errors_rate           │
│  │                                                               │
│  └─ telegram_alerts                  ← Smart notifications       │
│      Anomalies, low completion, inactivity detected             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┬──────────────────────┐
        ↓                     ↓                      ↓
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  REAL-TIME   │    │   ADMIN API     │    │  BENEFITS MATCH  │
│  DASHBOARD   │    │   ENDPOINTS     │    │  ENGINE          │
│              │    │                 │    │                  │
│ Charts       │    │ /api/telegram/* │    │ Auto-assess      │
│ Alerts       │    │ /api/telegram/  │    │ eligibility      │
│ Exports      │    │   monitor/*     │    │ Personalized     │
│              │    │                 │    │ recommendations  │
└──────────────┘    └─────────────────┘    └──────────────────┘
```

---

## 🔗 STEP 1: Link Bot Token to Your Backend

### Option A: Set Up in Railway (Production)

1. **Open Railway Dashboard**
   - Go to: https://railway.com/project/4396a56b-ff26-4b1a-a645-017541463f36
   - Select "MapleJourney" service
   - Click "Variables" tab

2. **Create Telegram Bot (If You Haven't)**
   ```
   Open Telegram → Search @BotFather
   /newbot
   Name: MapleJourney Collector Bot
   Username: maplejourney_collector_bot
   ✅ Get token: 123456789:ABCdefGHIjklmnoPQRstuvWXyz
   ```

3. **Add Environment Variable in Railway**
   ```
   Variable Name:    TELEGRAM_BOT_TOKEN
   Variable Value:   123456789:ABCdefGHIjklmnoPQRstuvWXyz
   
   Click "Add"
   ```

4. **Optional: Add Admin Settings**
   ```
   Variable Name:    TELEGRAM_ADMIN_CHAT_ID
   Variable Value:   [your Telegram user ID from @userinfobot]
   ```

5. **Deploy**
   ```
   git push origin main
   Railway auto-deploys (~2 minutes)
   ```

### Option B: Local Development

1. **Update backend/.env**
   ```
   TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnoPQRstuvWXyz"
   TELEGRAM_ADMIN_CHAT_ID="1234567890"
   ```

2. **Restart Backend**
   ```
   python backend/server.py
   # Or: uvicorn backend.server:app --reload
   ```

---

## 📊 STEP 2: Understand Your Data Structure

### When User Submits via Telegram

Data is stored in MongoDB as:

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": 123456789,
  "form_type": "profile",
  "timestamp": "2026-07-05T14:30:00Z",
  "data": {
    "email": "john@example.com",
    "phone": "+1-647-555-0100",
    "address": "123 Main St, Toronto, ON M5V 3A8",
    "full_name": "John Smith",
    "immigration_status": "Permanent Resident",
    "annual_income": 45000,
    "dependent_children": 2
  },
  "verified": false,
  "verified_by": null,
  "verified_at": null,
  "errors": 0,
  "collection_duration_seconds": 180,
  "user_agent": "Telegram Bot API"
}
```

**Key Fields for Scaling:**
- `_id` - Unique record ID for querying
- `user_id` - Links to same user across multiple forms
- `form_type` - Organize by benefit type
- `timestamp` - Time-series analysis
- `data` - The actual collected values
- `verified` - Admin verification flag

---

## 🚀 STEP 3: Extract Data as You Scale

### Real-Time API Endpoints (No Code Needed)

**Get Statistics:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/telegram/status

Response:
{
  "total_records": 1250,
  "completed": 1250,
  "today": 45,
  "by_form_type": {
    "profile": 500,
    "housing": 350,
    "jobs": 250,
    "education": 150
  }
}
```

**Export All Data as CSV:**
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2026-01-01",
    "date_to": "2026-12-31",
    "form_types": ["profile", "housing"]
  }' \
  https://api.example.com/api/telegram/export

Response: CSV file with all records
```

**Get Single User's Data:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/telegram/data/123456789

Response:
{
  "user_id": 123456789,
  "submissions": [
    { form_type: "profile", data: {...}, timestamp: "..." },
    { form_type: "housing", data: {...}, timestamp: "..." }
  ]
}
```

**Get Real-Time Metrics:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/telegram/monitor/metrics

Response:
{
  "collections_today": 45,
  "active_sessions": 12,
  "avg_completion_time": 240,
  "field_completion": {
    "email": 98.2,
    "phone": 97.5,
    "address": 96.1,
    ...
  }
}
```

---

## 💾 STEP 4: Direct MongoDB Querying (Advanced Scaling)

### When You Need Custom Analysis

**Count All Submissions:**
```javascript
db.telegram_collected_data.countDocuments()
// Result: 1250
```

**Find by Date Range:**
```javascript
db.telegram_collected_data.find({
  timestamp: {
    $gte: new Date("2026-07-01"),
    $lte: new Date("2026-07-31")
  }
})
```

**Group by Form Type:**
```javascript
db.telegram_collected_data.aggregate([
  {
    $group: {
      _id: "$form_type",
      count: { $sum: 1 },
      avg_income: { $avg: "$data.annual_income" }
    }
  }
])
```

**Find High-Income Applicants (for targeting):**
```javascript
db.telegram_collected_data.find({
  "data.annual_income": { $gte: 50000 }
}).limit(100)
```

**Export Ready-to-Verify Data:**
```javascript
db.telegram_collected_data.find({
  verified: false
}).project({
  user_id: 1,
  form_type: 1,
  data: 1,
  timestamp: 1
}).limit(50)
```

---

## 📈 STEP 5: Scaling as You Grow

### Phase 1: Startup (1,000-10,000 users)
```
✅ Current Setup
├─ Single MongoDB instance
├─ Real-time metrics (60-second intervals)
├─ CSV export capability
├─ Dashboard for monitoring
└─ API endpoints for integration
```

### Phase 2: Growth (10,000-100,000 users)
```
📊 Recommended Upgrades:
├─ Add database indexes on:
│  ├─ telegram_collected_data.user_id
│  ├─ telegram_collected_data.timestamp
│  ├─ telegram_collected_data.form_type
├─ Implement metrics aggregation (5-min buckets instead of 60-sec)
├─ Add background job queue for exports
├─ Implement data archival (old data → cold storage)
└─ Scale API servers from 1 → 3 replicas
```

**Add Indexes (One-Time):**
```javascript
// In MongoDB console
db.telegram_collected_data.createIndex({ user_id: 1 })
db.telegram_collected_data.createIndex({ timestamp: -1 })
db.telegram_collected_data.createIndex({ form_type: 1 })
db.telegram_collected_data.createIndex({ "data.email": 1 })
```

### Phase 3: Enterprise (100,000+ users)
```
🏢 Infrastructure:
├─ MongoDB Sharding (partition by user_id)
├─ Data Warehouse (BigQuery/Snowflake for analysis)
├─ Event Streaming (Kafka for real-time processing)
├─ API Rate Limiting & Caching
├─ Regional Deployment (handle international users)
└─ Multi-bot support (Telegram + WhatsApp + SMS)
```

---

## 🔄 STEP 6: Connect to Benefits Matching

Once you have user data, automatically match benefits:

```python
# After user submits via Telegram
user_data = await db.telegram_collected_data.find_one({
  "_id": ObjectId("...")
})

# Send to benefits engine
response = await requests.post(
  "https://api.example.com/api/benefits/assess-my-eligibility",
  json={
    "annual_income": user_data["data"]["annual_income"],
    "dependents": user_data["data"]["dependent_children"],
    "province": "Ontario",
    "immigration_status": user_data["data"]["immigration_status"]
  },
  headers={"Authorization": f"Bearer {token}"}
)

# Results: [
#   { "benefit": "CCB", "monthly": 350 },
#   { "benefit": "GIS", "monthly": 200 },
#   ...
# ]
```

---

## 🎯 Quick Reference: All Your Endpoints

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/telegram/status` | GET | Collection statistics | Admin |
| `/api/telegram/data/{user_id}` | GET | Get user's data | Admin |
| `/api/telegram/latest` | GET | Recent submissions | Admin |
| `/api/telegram/export` | POST | CSV export | Admin |
| `/api/telegram/metrics` | GET | Real-time metrics | Admin |
| `/api/telegram/monitor/` | GET | Dashboard data | Admin |
| `/api/telegram/monitor/alerts` | GET | Active alerts | Admin |
| `/api/telegram/monitor/trends` | GET | Historical trends | Admin |

---

## ✅ Verification Checklist

- [ ] Telegram bot created with @BotFather
- [ ] Bot token added to Railway environment variables
- [ ] Backend redeployed (`git push origin main`)
- [ ] Test bot: Search bot in Telegram → Send `/start`
- [ ] Test collection: Send `/collect` → Fill form
- [ ] Verify in API: `curl /api/telegram/status`
- [ ] Dashboard shows real-time data
- [ ] CSV export works
- [ ] Monitor endpoints responding

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check Railway logs: `railway logs --service MapleJourney` |
| Data not saving | Verify MongoDB connection in `.env` |
| Metrics empty | Wait 60 seconds, check `/api/telegram/metrics` |
| High latency | Add database indexes (see Phase 2) |
| API 403 Forbidden | Ensure user has `is_admin: true` in database |

---

## 📞 Support

**Check Logs:**
```
railway logs --service MapleJourney --tail 50
```

**Manual Test Bot:**
```
Open Telegram → Search @maplejourney_collector_bot
/start
/collect
Choose "Quick Profile"
Fill out the form
Submit
```

**Verify Data Saved:**
```
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/telegram/status
```

---

## 🎉 Summary

Your data pipeline is now:

✅ **Collecting** - Telegram bot gathers structured data  
✅ **Storing** - MongoDB vault with organized collections  
✅ **Monitoring** - Real-time alerts & metrics  
✅ **Exporting** - CSV, API endpoints, custom queries  
✅ **Integrating** - Ready for benefits matching  
✅ **Scaling** - Architecture ready for 10,000+ users  

**You now have professional-grade data infrastructure.**

All user data is securely stored, easily accessible, and scales with your growth.

---

*Last Updated: 2026-07-05*  
*Version: Production Ready*
