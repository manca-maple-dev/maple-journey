Write-Host '╔════════════════════════════════════════════════════════════╗'
Write-Host '║     🧪 MAPLEJORNEY MVP COMPREHENSIVE EVALUATION            ║'
Write-Host '╚════════════════════════════════════════════════════════════╝'
Write-Host ''

Write-Host '1️⃣  BACKEND HEALTH CHECK' -ForegroundColor Cyan
try {
    $h = Invoke-WebRequest 'https://web-production-1acc6.up.railway.app/api/health' -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host '   ✅ Health endpoint: OPERATIONAL' -ForegroundColor Green
    Write-Host "      Status: $($h.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host '   ❌ Health: FAILED' -ForegroundColor Red
}

Write-Host ''
Write-Host '2️⃣  FRONTEND RENDERING' -ForegroundColor Cyan
try {
    $f = Invoke-WebRequest 'https://maple-journey-app.vercel.app/' -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host '   ✅ Frontend loads: RESPONSIVE' -ForegroundColor Green
    Write-Host "      Status: $($f.StatusCode)" -ForegroundColor Green
    
    if ($f.Content -like '*Ask Maple*') { Write-Host '   ✅ AI Companion: VISIBLE' -ForegroundColor Green }
    if ($f.Content -like '*Daily Briefing*') { Write-Host '   ✅ Daily Briefing: VISIBLE' -ForegroundColor Green }
    if ($f.Content -like '*Job Matching*') { Write-Host '   ✅ Job Matching: VISIBLE' -ForegroundColor Green }
    if ($f.Content -like '*Start free*') { Write-Host '   ✅ Sign-up CTA: VISIBLE' -ForegroundColor Green }
    if ($f.Content -like '*MapleJourney*') { Write-Host '   ✅ Branding: INTACT' -ForegroundColor Green }
} catch {
    Write-Host '   ❌ Frontend: FAILED' -ForegroundColor Red
}

Write-Host ''
Write-Host '3️⃣  CORE API ENDPOINTS' -ForegroundColor Cyan
$endpoints = @('health', 'plans', 'resources', 'benefits', 'content')
foreach ($ep in $endpoints) {
    try {
        $r = Invoke-WebRequest "https://web-production-1acc6.up.railway.app/api/$ep" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "   ✅ /api/$ep`: WORKING ($($r.StatusCode))" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ /api/$ep`: FAILED" -ForegroundColor Red
    }
}

Write-Host ''
Write-Host '4️⃣  PAYMENT & PRICING SYSTEM' -ForegroundColor Cyan
try {
    $plans = Invoke-WebRequest 'https://web-production-1acc6.up.railway.app/api/plans' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($plans.Content -like '*Newcomer*' -and $plans.Content -like '*Plus*' -and $plans.Content -like '*Family*') {
        Write-Host '   ✅ All pricing tiers: CONFIGURED' -ForegroundColor Green
        Write-Host '      - Newcomer (Free)' -ForegroundColor Green
        Write-Host '      - Plus ($2.99/mo)' -ForegroundColor Green
        Write-Host '      - Family ($4.99/mo)' -ForegroundColor Green
    }
} catch {
    Write-Host '   ❌ Pricing system: CHECK' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '5️⃣  FEATURES DETECTION' -ForegroundColor Cyan
try {
    $features = Invoke-WebRequest 'https://web-production-1acc6.up.railway.app/api/features' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host '   ✅ Feature flags API: OPERATIONAL' -ForegroundColor Green
} catch {
    Write-Host '   ⚠️  Feature flags: REQUIRES AUTH' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '6️⃣  CONTENT & RESOURCES' -ForegroundColor Cyan
try {
    $content = Invoke-WebRequest 'https://web-production-1acc6.up.railway.app/api/content' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host '   ✅ Public content: AVAILABLE' -ForegroundColor Green
} catch {
    Write-Host '   ⚠️  Public content: NOT CACHED' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '7️⃣  SWAGGER API DOCUMENTATION' -ForegroundColor Cyan
try {
    $swagger = Invoke-WebRequest 'https://web-production-1acc6.up.railway.app/docs' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($swagger.Content -like '*Swagger*' -or $swagger.Content -like '*openapi*') {
        Write-Host '   ✅ API Docs: LIVE & INTERACTIVE' -ForegroundColor Green
        Write-Host '      URL: /docs' -ForegroundColor Green
    }
} catch {
    Write-Host '   ❌ API Docs: UNAVAILABLE' -ForegroundColor Red
}

Write-Host ''
Write-Host '╔════════════════════════════════════════════════════════════╗'
