$ErrorActionPreference = 'Stop'

$base = 'https://web-production-1acc6.up.railway.app'
$api = "$base/api"
$password = 'MapleQa!2026#'
$ts = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$email = "health.check.$ts@maplejourney.app"

Write-Host '=== MAPLE PROD HEALTH CHECK ==='

# 1) Docs
$docs = Invoke-WebRequest -Uri "$base/docs" -UseBasicParsing -TimeoutSec 30
Write-Host ("DOCS_HTTP=" + [int]$docs.StatusCode)

# 2) Register/Login
$regBody = @{ name = 'Prod Health'; email = $email; password = $password } | ConvertTo-Json
try {
  Invoke-WebRequest -Uri ($api + '/auth/register') -Method Post -ContentType 'application/json' -Body $regBody -UseBasicParsing -TimeoutSec 30 | Out-Null
} catch {
  # user may already exist in retry scenarios
}

$loginBody = @{ email = $email; password = $password } | ConvertTo-Json
$loginResp = Invoke-WebRequest -Uri ($api + '/auth/login') -Method Post -ContentType 'application/json' -Body $loginBody -UseBasicParsing -TimeoutSec 30
$loginJson = $loginResp.Content | ConvertFrom-Json
$token = $loginJson.token
if (-not $token) { $token = $loginJson.access_token }
if (-not $token) { throw 'AUTH_TOKEN_MISSING' }
Write-Host ("AUTH_HTTP=" + [int]$loginResp.StatusCode)

$authHeaders = @{ Authorization = ('Bearer ' + $token); 'Content-Type' = 'application/json' }

# 3) Checkout
$checkoutBody = @{ plan_id = 'plus' } | ConvertTo-Json
$checkoutResp = Invoke-WebRequest -Uri ($api + '/checkout/session') -Method Post -Headers $authHeaders -Body $checkoutBody -UseBasicParsing -TimeoutSec 60
$checkoutJson = $checkoutResp.Content | ConvertFrom-Json
Write-Host ("CHECKOUT_HTTP=" + [int]$checkoutResp.StatusCode)
Write-Host ("CHECKOUT_URL_PRESENT=" + [bool]($checkoutJson.url -match '^https://checkout.stripe.com/'))

# 4) Jobs
$jobsResp = Invoke-WebRequest -Uri ($api + '/jobs/search?location=Toronto&keywords=developer&limit=10&refresh=true') -Headers @{ Authorization = ('Bearer ' + $token) } -UseBasicParsing -TimeoutSec 90
$jobsJson = $jobsResp.Content | ConvertFrom-Json
Write-Host ("JOBS_HTTP=" + [int]$jobsResp.StatusCode)
Write-Host ("JOBS_COUNT=" + $jobsJson.count)
if ($jobsJson.jobs) {
  $jobsJson.jobs | Select-Object -First 3 | ForEach-Object {
    Write-Host ("JOB_SOURCE=" + $_.source + ' | JOB_TITLE=' + $_.title)
  }
}

Write-Host '=== HEALTH CHECK COMPLETE ==='
