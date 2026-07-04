# Live Testing Before Deployment (Watch Tester In Real Time)

This project now supports two live testing modes:

1. Human tester session watching (OpenReplay)
2. Automated tester takeover runs (Playwright UI)

## 1) Human Tester Session Watching (OpenReplay)

### Installed
- `@openreplay/tracker` in frontend
- Bootstrap file: `frontend/src/lib/liveSessionTracker.js`
- Startup hook: `frontend/src/index.js`

### Enable it
1. Copy `frontend/.env.live-testing.example` values into your active `frontend/.env`.
2. Set:
   - `REACT_APP_ENABLE_LIVE_SESSION_REPLAY=true`
   - `REACT_APP_OPENREPLAY_PROJECT_KEY=<your key>`
3. Start frontend:
```powershell
cd "$env:USERPROFILE\maple-journey-dev\frontend"
corepack yarn start
```
4. Open OpenReplay dashboard and watch tester sessions live.

## 2) Automated Tester Takeover (Playwright)

### Installed
- `@playwright/test` as dev dependency
- Config: `frontend/playwright.config.js`
- Live explorer spec: `frontend/tests/live/app-explore.spec.js`

### First-time browser install
```powershell
cd "$env:USERPROFILE\maple-journey-dev\frontend"
npx playwright install
```

### Run live interactive mode (you can watch actions)
```powershell
cd "$env:USERPROFILE\maple-journey-dev\frontend"
corepack yarn test:live
```

### Run headed takeover mode
```powershell
cd "$env:USERPROFILE\maple-journey-dev\frontend"
corepack yarn test:watch
```

## Recommended pre-deploy flow
1. Start backend and frontend.
2. Run Playwright live mode to explore critical routes.
3. Have a human tester navigate onboarding/chat/jobs while OpenReplay records.
4. Check `backend/scripts/launch_qa_matrix.ps1` after fixes.
5. Deploy only if both automated and human-session checks are clean.
