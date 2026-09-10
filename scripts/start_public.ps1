param(
    [int]$Port = 8501,
    [string]$Password = "",
    # Some corporate browsers/proxies block the Streamlit WebSocket handshake
    # used by a Cloudflare Quick Tunnel.  This scoped mode relaxes CORS for the
    # temporary, password-protected URL only; it does not change local defaults.
    [switch]$CompatibilityMode
)

$ErrorActionPreference = "Stop"
$ProjectPath = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectPath ".venv\Scripts\python.exe"
$PythonPath = if (Test-Path -LiteralPath $VenvPython) {
    $VenvPython
} else {
    "C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
}
$CloudflaredPath = Join-Path $ProjectPath "tools\cloudflared.exe"

if (-not (Test-Path -LiteralPath $CloudflaredPath)) {
    throw "cloudflared.exe not found at $CloudflaredPath"
}
if ([string]::IsNullOrWhiteSpace($Password)) {
    $Password = "CQ-" + [guid]::NewGuid().ToString("N").Substring(0, 12)
}

$env:DASHBOARD_PASSWORD = $Password
$streamlitArgs = @("-m", "streamlit", "run", "streamlit_app.py", "--server.address=127.0.0.1", "--server.port=$Port", "--server.headless=true")
if ($CompatibilityMode) {
    # Streamlit documents these two switches for remote-loading failures caused
    # by proxy/CORS/WebSocket negotiation.  XSRF protection remains enabled.
    $streamlitArgs += "--server.enableCORS=false"
    $streamlitArgs += "--server.enableWebsocketCompression=false"
}
$process = Start-Process -FilePath $PythonPath -ArgumentList $streamlitArgs -WorkingDirectory $ProjectPath -WindowStyle Hidden -PassThru

Write-Host "Dashboard password: $Password"
Write-Host "Streamlit PID: $($process.Id)"
if ($CompatibilityMode) {
    Write-Host "Compatibility mode: enabled (temporary tunnel CORS relaxed; XSRF protection remains enabled)."
}
Write-Host "Starting temporary Cloudflare URL. Keep this window open."
& $CloudflaredPath tunnel --url "http://127.0.0.1:$Port"
