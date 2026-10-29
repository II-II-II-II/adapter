# Adapter -- start the local chat window.
#
# Don't run this directly. Double-click "Start Adapter.bat" instead.
#
# Starts Ollama (the AI) and Open WebUI (the chat window), waits until the
# window is genuinely ready, then opens your browser. Everything the server
# prints goes to logs\start.log -- which is where the reason lives if the
# browser comes up blank.

$ErrorActionPreference = "Continue"   # a server crash should log, not vanish

. (Join-Path $PSScriptRoot "_log.ps1")

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Start-AdapterLog "start"

trap {
    Log "UNHANDLED $($_.Exception.Message)"
    Log "AT $($_.InvocationInfo.PositionMessage)"
    Write-Host ""
    Write-Host "Couldn't start. $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Double-click 'Share My Log.bat' and send the file."
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Adapter" -ForegroundColor Cyan
Write-Host ""

$vpy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) {
    Log "venv missing at $vpy"
    Write-Host "This isn't set up yet." -ForegroundColor Yellow
    Write-Host "Double-click 'Setup Adapter.bat' first."
    Read-Host "Press Enter to close"
    exit 1
}

# Already running? Opening a second one fails with a confusing port error.
$busy = $false
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 3 -UseBasicParsing
    $busy = $true
} catch { }
if ($busy) {
    Log "port 8080 already serving -- reusing"
    Ok "Already running. Opening your browser."
    Start-Process "http://localhost:8080"
    Write-Host ""
    Write-Host "If you want to restart it, close the other black window first."
    Read-Host "Press Enter to close"
    exit 0
}

Step "Starting the AI"
$running = $false
try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -UseBasicParsing
    $running = $true
    Ok "Ollama was already running"
} catch { }

if (-not $running) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    for ($i = 0; $i -lt 15; $i++) {
        Start-Sleep -Seconds 1
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -UseBasicParsing
            $running = $true; break
        } catch { }
    }
    if ($running) { Ok "Ollama started" } else { Warn "Ollama didn't start -- the chat will load but won't answer" }
}
Log "ollama running: $running"

if ($running) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 5 -UseBasicParsing
        $names = (ConvertFrom-Json $r.Content).models | ForEach-Object { $_.name }
        if ($names) { Ok "Model: $($names[0])"; Log "models: $($names -join ', ')" }
        else { Warn "No model downloaded. In a Command Prompt run:  ollama pull qwen2.5:14b" }
    } catch { }
}

Step "Starting your chat window"
Write-Host ""
Write-Host "  Leave this black window OPEN while you work." -ForegroundColor Yellow
Write-Host "  Closing it shuts the chat down."
Write-Host ""
Write-Host "  Your browser opens by itself once it's ready -- usually 20-60"
Write-Host "  seconds the first time. Nothing to click until then."
Write-Host ""

# Open the browser when the server actually answers, not after a blind wait.
# A fixed sleep opens a browser on a dead port and looks like a failure.
$poll = @'
for ($i = 0; $i -lt 180; $i++) {
  Start-Sleep -Seconds 1
  try { $null = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 2 -UseBasicParsing
        Start-Process "http://localhost:8080"; exit } catch { }
}
'@
Start-Process -FilePath "powershell" -WindowStyle Hidden `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $poll) `
    -ErrorAction SilentlyContinue

Log "launching: $vpy -m open_webui serve"
Write-Host "  (server messages below are also saved to logs\start.log)" -ForegroundColor DarkGray
Write-Host ""

# ForEach-Object, not Tee-Object: Tee buffers, and on a server that runs for
# hours you'd see nothing until it exited.
& $vpy -m open_webui serve 2>&1 | ForEach-Object {
    $line = "$_"
    Write-Host $line
    try { Add-Content -Path $global:AdapterLog -Value $line -Encoding utf8 } catch { }
}

$code = $LASTEXITCODE
Log "open_webui exited with $code"

Write-Host ""
if ($code -ne 0) {
    Write-Host "The chat window stopped unexpectedly (code $code)." -ForegroundColor Red
    Write-Host "The reason is at the bottom of logs\start.log."
    Write-Host "Double-click 'Share My Log.bat' and send the file."
} else {
    Write-Host "Chat window closed." -ForegroundColor Gray
}
Write-Host ""
Read-Host "Press Enter to close"
