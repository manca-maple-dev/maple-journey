$frontend = if ($env:MAPLE_FRONTEND_URL) { $env:MAPLE_FRONTEND_URL } else { "http://localhost:3000" }
$backend = if ($env:MAPLE_BACKEND_URL) { $env:MAPLE_BACKEND_URL } else { "http://127.0.0.1:8000" }

$checks = @(
  @{ Name = "Auth page"; Url = "$frontend/login"; IsFrontend = $true },
  @{ Name = "Signup page"; Url = "$frontend/signup"; IsFrontend = $true },
  @{ Name = "Onboarding"; Url = "$frontend/app/onboarding"; IsFrontend = $true },
  @{ Name = "Chat"; Url = "$frontend/app/chat"; IsFrontend = $true },
  @{ Name = "Jobs"; Url = "$frontend/app/jobs"; IsFrontend = $true },
  @{ Name = "Privacy"; Url = "$frontend/privacy"; IsFrontend = $true },
  @{ Name = "Terms"; Url = "$frontend/terms"; IsFrontend = $true },
  @{ Name = "Cookies"; Url = "$frontend/cookies"; IsFrontend = $true },
  @{ Name = "Disclaimer"; Url = "$frontend/disclaimer"; IsFrontend = $true },
  @{ Name = "API health"; Url = "$backend/api/health"; IsFrontend = $false },
  @{ Name = "Ops health"; Url = "$backend/api/ops/health"; IsFrontend = $false },
  @{ Name = "Ops readiness"; Url = "$backend/api/ops/ready"; IsFrontend = $false },
  @{ Name = "Messaging config"; Url = "$backend/api/messaging/config"; IsFrontend = $false },
  @{ Name = "Webhook status"; Url = "$backend/api/webhook/status"; IsFrontend = $false }
)

$results = @()
foreach ($check in $checks) {
  try {
    $headers = if ($check.IsFrontend) { @{ Accept = "text/html" } } else { @{} }
    $resp = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 8 -Headers $headers
    $results += [PSCustomObject]@{ Name = $check.Name; Url = $check.Url; Status = "PASS"; Code = $resp.StatusCode }
  } catch {
    $code = if ($_.Exception.Response) { $_.Exception.Response.StatusCode.value__ } else { 0 }
    $results += [PSCustomObject]@{ Name = $check.Name; Url = $check.Url; Status = "FAIL"; Code = $code }
  }
}

$results | Format-Table -AutoSize

$failed = ($results | Where-Object { $_.Status -eq "FAIL" }).Count
if ($failed -gt 0) {
  Write-Host "\nQA Matrix: FAIL ($failed failed checks)"
  exit 1
}

Write-Host "\nQA Matrix: PASS"
