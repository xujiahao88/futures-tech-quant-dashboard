param(
    [int]$Port = 8501,
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"
$ProjectPath = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Virtual environment Python not found at $VenvPython"
}

$existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    throw "Port $Port is already in use by PID $($existing.OwningProcess)."
}

$RuntimePath = Join-Path $ProjectPath "reports\runtime"
New-Item -ItemType Directory -Path $RuntimePath -Force | Out-Null
$StdoutPath = Join-Path $RuntimePath "streamlit-local.stdout.log"
$StderrPath = Join-Path $RuntimePath "streamlit-local.stderr.log"
$PidPath = Join-Path $RuntimePath "streamlit-local.pid"

$env:DASHBOARD_PASSWORD = $Password
$streamlitArgs = @(
    "-m", "streamlit", "run", "streamlit_app.py",
    "--server.address=127.0.0.1",
    "--server.port=$Port",
    "--server.headless=true",
    "--server.fileWatcherType=none"
)
$startArgs = @{
    FilePath = $VenvPython
    ArgumentList = $streamlitArgs
    WorkingDirectory = $ProjectPath
    WindowStyle = "Hidden"
    RedirectStandardOutput = $StdoutPath
    RedirectStandardError = $StderrPath
    PassThru = $true
}
$process = Start-Process @startArgs

Set-Content -LiteralPath $PidPath -Value $process.Id -Encoding ascii

$HealthUrl = "http://127.0.0.1:$Port/_stcore/health"
$healthy = $false
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 2
        if ($response.StatusCode -eq 200 -and $response.Content.Trim() -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        # The server can take a few seconds to bind the port.
    }
}

if (-not $healthy) {
    throw "Streamlit failed its startup health check. See $StderrPath"
}

Write-Host "Dashboard URL: http://127.0.0.1:$Port"
Write-Host "Launcher PID: $($process.Id)"
Write-Host "Health check: PASS"
if (-not [string]::IsNullOrWhiteSpace($Password)) {
    Write-Host "Password protection: enabled"
}
