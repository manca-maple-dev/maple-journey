param(
  [switch]$BackendOnly,
  [switch]$FrontendOnly
)

$root = Join-Path $env:USERPROFILE "maple-journey-dev"
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

function Stop-PortOwner([int]$Port) {
  $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($conn -and $conn.OwningProcess) {
    try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
  }
}

function Start-Backend() {
  Stop-PortOwner 8000
  Set-Location $backend
  Start-Process -FilePath ".\\venv\\Scripts\\python.exe" -ArgumentList "server.py" -WorkingDirectory $backend | Out-Null
}

function Start-Frontend() {
  Stop-PortOwner 3000
  Set-Location $frontend
  Start-Process -FilePath "C:\\Program Files\\nodejs\\corepack.cmd" -ArgumentList "yarn","start" -WorkingDirectory $frontend | Out-Null
}

if (-not $FrontendOnly) { Start-Backend }
if (-not $BackendOnly) { Start-Frontend }

Write-Host "Dev services started with process guardrails."