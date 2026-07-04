# MapleJourney Production Deployment Guide

## 1) Runtime stability (one command per service)

### Start
```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/dev_start.ps1
```

### Stop
```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/dev_stop.ps1
```

These scripts enforce single-process guardrails for backend/frontend ports.

## 2) Replace temporary tunnel with permanent URL

Use a permanent backend domain with TLS (e.g. `https://api.maplejourney.ca`).

Set env:
```env
WEBHOOK_BASE_URL=https://api.maplejourney.ca
```

Point Twilio webhooks once:
- WhatsApp: `POST https://api.maplejourney.ca/api/webhook/whatsapp-webhook`
- SMS/iMessage: `POST https://api.maplejourney.ca/api/webhook/imessage-webhook`

## 3) Deployment pipeline gates

Workflow file: `.github/workflows/deploy-gates.yml`

Gates include:
- backend compile
- frontend build
- backend smoke start
- health/readiness checks (`/api/health`, `/api/ops/health`, `/api/ops/ready`)
- fail deploy on gate failure

## 4) Observability minimum set

New endpoints:
- `GET /api/ops/health`
- `GET /api/ops/ready`
- `GET /api/ops/metrics`

Track:
- error rate
- avg/max latency
- webhook dedup markers per day
- uptime

## 5) Final launch QA matrix

Run manual checks:
- Auth: login/signup/logout
- Onboarding flow
- Chat (web)
- Jobs page
- Cookie consent on website routes only
- Legal pages (`/privacy`, `/terms`, `/cookies`, `/disclaimer`)
- WhatsApp inbound/outbound
- iMessage/SMS inbound/outbound
- Payment tier retrieval and checkout path
