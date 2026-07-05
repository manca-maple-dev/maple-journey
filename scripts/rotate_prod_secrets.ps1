Param(
  [string]$ProjectId = "4396a56b-ff26-4b1a-a645-017541463f36",
  [string]$EnvironmentId = "f1cf66e3-ead7-4266-a6db-ed91e93a0f85",
  [string]$Service = "web",
  [switch]$Apply,
  [switch]$SkipRedeploy,
  [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

function Require-Tool {
  Param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required tool '$Name' was not found in PATH."
  }
}

function Get-SecretInput {
  Param([string]$Key)
  $secure = Read-Host -Prompt "Enter new value for $Key" -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  }
}

Require-Tool -Name "railway"

Write-Host "=== Maple Production Secret Rotation ==="
Write-Host "Project: $ProjectId"
Write-Host "Environment: $EnvironmentId"
Write-Host "Service: $Service"
$mode = "DRY-RUN"
if ($Apply) {
  $mode = "APPLY"
}
Write-Host "Mode: $mode"

$rotationOrder = @(
  "STRIPE_API_KEY",
  "OPENAI_API_KEY",
  "EMERGENT_LLM_KEY",
  "SMTP_PASSWORD",
  "ADMIN_PASSWORD",
  "JWT_SECRET"
)

if (-not $Apply) {
  Write-Host ""
  Write-Host "Dry run only. No values will be changed."
  Write-Host "Run with -Apply to execute rotation."
  Write-Host "Rotation order:"
  $rotationOrder | ForEach-Object { Write-Host " - $_" }
  exit 0
}

Write-Host ""
Write-Host "Collecting new values interactively (not echoed)..."
$updates = @{}
foreach ($key in $rotationOrder) {
  $updates[$key] = Get-SecretInput -Key $key
}

Write-Host ""
Write-Host "Applying secret updates..."
foreach ($key in $rotationOrder) {
  $value = $updates[$key]
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "Empty value provided for $key. Aborting."
  }

  # Use JSON output for deterministic command success signal; do not print values.
  $result = railway variable set "$key=$value" `
    -p $ProjectId `
    -e $EnvironmentId `
    -s $Service `
    --json

  if (-not $result) {
    throw "railway variable set returned no output for $key"
  }

  Write-Host "Updated $key"
}

if (-not $SkipRedeploy) {
  Write-Host ""
  Write-Host "Triggering redeploy by setting ROTATED_AT marker..."
  $stamp = [DateTimeOffset]::UtcNow.ToString("o")
  railway variable set "ROTATED_AT=$stamp" `
    -p $ProjectId `
    -e $EnvironmentId `
    -s $Service `
    --json | Out-Null
  Write-Host "Redeploy marker applied."
}

if (-not $SkipHealthCheck) {
  Write-Host ""
  Write-Host "Running production health check..."
  $scriptPath = Join-Path (Split-Path -Parent $PSScriptRoot) "scripts\prod_health_check.ps1"
  if (-not (Test-Path $scriptPath)) {
    throw "Health check script not found at $scriptPath"
  }

  powershell -ExecutionPolicy Bypass -File $scriptPath
}

Write-Host ""
Write-Host "Rotation flow complete."
