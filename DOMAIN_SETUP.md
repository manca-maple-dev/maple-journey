# MapleJourney.ca Domain Setup Guide

## What's Been Done ✅
1. Created `.env.production` for Vercel with API backend URL
2. Created `vercel.json` configuration for production deployment
3. Updated all files needed for domain deployment

## Manual Steps Required (Complete These in Your Domain Registrar)

### Step 1: Point maplejourney.ca to Vercel
Go to your domain registrar's DNS settings and add these records:

**Option A: Using CNAME (Recommended for subdomains)**
- Type: CNAME
- Name: www (or @ for root)
- Value: cname.vercel.com.

**Option B: Using A/AAAA Records (For root domain @)**
- Type: A
- Name: @ (root domain)
- Value: 76.76.19.165

- Type: AAAA
- Name: @
- Value: 2606:4700:4700::1111

### Step 2: Add Domain to Vercel
1. Go to Vercel Dashboard → maple-journey-app → Settings → Domains
2. Click "Add Domain"
3. Enter: **maplejourney.ca**
4. Follow Vercel's DNS verification steps
5. Also add: **www.maplejourney.ca** (as alias/redirect)

### Step 3: Configure Vercel Environment Variables
In Vercel Console for maple-journey-app:
- Go to Settings → Environment Variables
- Add: `REACT_APP_BACKEND_URL` = `https://api.maplejourney.ca`

### Step 4: Point API Subdomain to Railway (Backend)
In your domain registrar DNS settings:
- Type: CNAME
- Name: api
- Value: web-production-1acc6.up.railway.app.

Then in Railway Console:
- Go to your backend service settings
- Add custom domain: **api.maplejourney.ca**
- Wait for SSL certificate to auto-generate (2-5 mins)

### Step 5: Deploy Frontend
Push to main branch:
```bash
git push origin main
```
Vercel will auto-deploy to maplejourney.ca

### Step 6: Verify Setup
After DNS propagates (5-30 mins):
1. Visit https://maplejourney.ca
2. Check browser console for API calls to https://api.maplejourney.ca
3. Test chat feature to verify API connection works

## DNS Propagation Timeline
- Immediate: Changes take effect (but cached versions may persist)
- 5-30 minutes: Most DNS resolvers updated
- Up to 48 hours: Full global propagation

## Troubleshooting

**Domain shows 404 on Vercel:**
- Verify domain added in Vercel console
- Check DNS records point correctly
- Clear browser cache

**API calls fail to api.maplejourney.ca:**
- Verify CNAME points to railway.app domain
- Check Railway custom domain is verified (SSL cert generated)
- Review CORS settings in backend

**Email issues (SMTP with maplejourney.ca):**
- Update `SMTP_HOST` in backend to match your mail provider
- Verify SPF/DKIM/DMARC records in DNS for email delivery

## Environment Files Summary

**Frontend .env.production:**
```
REACT_APP_BACKEND_URL=https://api.maplejourney.ca
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=true
```

**Backend (Railway) - Already configured:**
- ADMIN_EMAIL: admin@maplejourney.ca
- SMTP settings configured for support@maplejourney.ca
- Ensure Railway has CORS_ORIGINS updated if needed

## Rollback (If Needed)
To revert to vercel.app domain:
1. In Vercel, remove custom domain
2. In code, revert .env.production changes
3. Push to main branch
