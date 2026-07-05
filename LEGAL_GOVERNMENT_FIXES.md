# Legal & Government Sections - Bug Fixes

## 🐛 Issues Found & Fixed

### Problem 1: No Separate Government Endpoint
- **Symptom:** Government resources weren't displayed separately from legal aid
- **Cause:** Only `/api/domain/legal-resources` endpoint existed
- **Fix:** Created dedicated `/api/domain/government-resources` endpoint

### Problem 2: Data Not Showing
- **Symptom:** Legal and Government sections showing empty
- **Cause:** Database collections might not be populated during startup
- **Fix:** Added improved seed with error handling and verification

### Problem 3: No Way to Diagnose Issues
- **Symptom:** No visibility into why data wasn't showing
- **Cause:** No diagnostic endpoints
- **Fix:** Added diagnostic endpoints to check and repopulate data

---

## ✅ Solutions Implemented

### 1. **New Legal & Government Endpoints**

#### GET /api/domain/legal-resources
```
Returns: Legal aid organizations and services
- Filtered by source_kind = "legal-aid"
- Includes: Pro Bono Ontario, Legal Aid BC, Legal Aid Alberta, etc.
```

#### GET /api/domain/government-resources  
```
Returns: Government agencies (IRCC, Justice, IRB, etc.)
- Filtered by source_kind = "government"  
- Includes: IRCC, Service Canada, immigration laws, etc.
```

Both endpoints:
- ✅ Rank by relevance to user's profile
- ✅ Show availability status
- ✅ Include contact information
- ✅ Sorted by freshness

---

### 2. **Diagnostic Endpoints**

#### GET /api/domain/diagnostics/data-status
**Purpose:** Check what data is currently in the database

**Returns:**
```json
{
  "legal_resources": {
    "total": 15,
    "government": 5,
    "legal_aid": 10,
    "by_kind": [...]
  },
  "source_registry": 15,
  "benefits": 6,
  "resources": 6,
  "status": "healthy" or "empty"
}
```

**Use cases:**
- Verify data is loaded after deployment
- Check before user reports missing data
- Monitor collection sizes

---

#### POST /api/domain/diagnostics/repopulate-legal-resources
**Purpose:** Force repopulate legal resources from scratch

**Does:**
1. Ensures source registry is populated
2. Clears existing legal_resources
3. Materializes fresh data from registry
4. Verifies data was created

**Returns:**
```json
{
  "ok": true,
  "message": "Legal resources repopulated successfully",
  "materialized": 15,
  "government_resources": 5,
  "legal_aid_resources": 10
}
```

**Use cases:**
- Fix empty Legal/Government sections
- Force refresh after updates
- Verify data integrity

---

### 3. **Improved Startup Process**

**Changes to seed.py:**
```python
# Before: Just called materialize and hoped
await ensure_source_registry(db)
await materialize_legal_resources_from_registry(db)

# After: Verify and retry
await ensure_source_registry(db)
legal_count = await materialize_legal_resources_from_registry(db)
logger.info(f"Legal resources materialized: {legal_count} sources")

existing_legal = await db.legal_resources.count_documents({})
if existing_legal == 0:
    logger.warning("No legal resources found. Reseeding...")
    await refresh_legal_sources_and_resources(db)
```

**Benefits:**
- Logs what happened during startup
- Automatically retries if data is empty
- Prevents deployment with empty collections

---

## 🔧 How to Use These Fixes

### Step 1: Check Data Status
```bash
curl -X GET \
  https://web-production-1acc6.up.railway.app/api/domain/diagnostics/data-status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected response (if healthy):
```json
{
  "legal_resources": {
    "total": 15,
    "government": 5,
    "legal_aid": 10
  },
  "status": "healthy"
}
```

### Step 2: If Status is "empty", Repopulate
```bash
curl -X POST \
  https://web-production-1acc6.up.railway.app/api/domain/diagnostics/repopulate-legal-resources \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Expected response:
```json
{
  "ok": true,
  "materialized": 15,
  "government_resources": 5,
  "legal_aid_resources": 10
}
```

### Step 3: Verify Fix
```bash
curl -X GET \
  https://web-production-1acc6.up.railway.app/api/domain/government-resources \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Should now return list of government resources.

---

## 📊 Data Available

### Government Resources (5 default)
- IRCC - Official immigration agency
- Justice Laws (IRPA) - Immigration law text
- Immigration and Refugee Board - Tribunal info
- Service Canada - General services
- Plus provincial variations

### Legal Aid Resources (10+ by province)
- Pro Bono Ontario - Free legal help
- Legal Aid BC - British Columbia support
- Legal Aid Alberta - Alberta support  
- Commission des services juridiques - Quebec support
- Plus national legal aid organizations

### Endpoint Counts
```
Source Registry:     15+ government/legal organizations
Legal Resources:     15+ materialized from registry
Government:          5+ government agencies
Legal Aid:           10+ legal aid providers
Benefits:            12+ government benefits
Resources:           6+ general resources
```

---

## 🆘 Troubleshooting

### Issue: Still seeing empty Legal/Government sections
**Solution:**
1. Run `/api/domain/diagnostics/data-status` to check
2. If empty, run `/api/domain/diagnostics/repopulate-legal-resources`
3. Wait 30 seconds and refresh frontend

### Issue: Getting 500 error on new endpoints
**Solution:**
1. Check backend logs: `railway logs --service MapleJourney`
2. Verify database connection is active
3. Run repopulate endpoint

### Issue: Only seeing government OR legal aid, not both
**Solution:**
1. Call both endpoints:
   - `/api/domain/government-resources`
   - `/api/domain/legal-resources`
2. Check diagnostics to verify both exist in database

---

## 📝 Updates Section - Live Notifications

As mentioned, the Updates section is designed for **live notifications about every update**:

```python
async def run_update_cycle(db) -> Dict[str, Any]:
    """Runs on schedule (every 6 hours default) and logs to db.update_runs"""
    # Checks: Legal resources, Government sources, Community data
    # Stores: Started time, finished time, any errors
```

### Check Update History
```bash
GET /api/domain/updates/runs?limit=20
```

Returns last 20 update cycles with:
- When they ran (started_at, finished_at)
- Status (ok: true/false)
- Any errors that occurred
- Counts of resources checked

### Run Updates Immediately (don't wait 6 hours)
```bash
POST /api/domain/updates/run
```

This triggers immediate refresh of:
- Legal resources database
- Government source health checks
- Community data cache

---

## ✨ Next Steps

1. **Immediate:** Run diagnostics to check current status
2. **If needed:** Use repopulate endpoint to fix empty sections
3. **Monitor:** Check update cycles are running (POST /api/domain/updates/run)
4. **Users:** Legal and Government sections should now display properly

---

## Git Commit

```
9c0024f - fix: Resolve Legal & Government data display bugs with diagnostics
```

**Changes:**
- domain.py: Added government endpoint + diagnostics (57 lines)
- seed.py: Improved error handling and verification (10 lines)
- Updated imports and added logging

All changes are backward compatible - no breaking changes to existing endpoints.
