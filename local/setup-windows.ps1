# Adapter -- Windows setup for a fully local install.
#
# Don't run this directly. Double-click "Setup Adapter.bat" instead.
#
# Installs: a Python virtual environment, GPU transcription, Ollama, a local
# chat model, and Open WebUI -- the chat window you'll actually talk to.
#
# Every step is written to logs\setup.log with its exit code. If this fails,
# that file is the thing to send.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # otherwise download bars spam the log

. (Join-Path $PSScriptRoot "_log.ps1")

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Start-AdapterLog "setup"

# A second, raw capture of the whole console. The helpers above log the things
# we thought to log; this catches the things we didn't.
try { Start-Transcript -Path (Join-Path $Root "logs\setup-transcript.log") -Force | Out-Null } catch { Log "transcript unavailable: $($_.Exception.Message)" }

trap {
    Log "UNHANDLED $($_.Exception.GetType().Name): $($_.Exception.Message)"
    Log "AT $($_.InvocationInfo.PositionMessage)"
    Write-Host ""
    Write-Host "Setup hit an error it didn't expect and stopped." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Nothing is broken -- you can run Setup Adapter.bat again safely."
    Write-Host "If it keeps failing, double-click 'Share My Log.bat' and send the file."
    Write-Host ""
    try { Stop-Transcript | Out-Null } catch { }
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Adapter setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "This takes 20-40 minutes, almost all of it downloading."
Write-Host "A lot of text will scroll past. That's normal -- you don't have to read it."
Write-Host "You can leave it running and come back."
Write-Host ""
Write-Host "Keeping a log at: logs\setup.log" -ForegroundColor Gray

Write-Environment

# -- Python ------------------------------------------------------------------
# open-webui requires Python 3.11 or 3.12. It does NOT work on 3.13, which is
# exactly what python.org's big download button gives you today. This is the
# single most common way this install fails.
Step "Looking for Python 3.11 or 3.12"

$pyExe = $null
$pyArgs = @()

foreach ($v in @("3.12", "3.11")) {
    try {
        $t = & py -$v -c "import sys; print(sys.version.split()[0])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $t) {
            $pyExe = "py"; $pyArgs = @("-$v")
            Ok "Found Python $t (via the py launcher)"
            break
        }
    } catch { }
}

if (-not $pyExe) {
    foreach ($cmd in @("python", "python3")) {
        try {
            $v = & $cmd -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and ($v -eq "3.12" -or $v -eq "3.11")) {
                $pyExe = $cmd; $pyArgs = @()
                Ok "Found Python $v"
                break
            } elseif ($v) {
                Warn "Found Python $v at '$cmd', which won't work here."
                Log "rejected python: $cmd reports $v"
            }
        } catch { }
    }
}

if (-not $pyExe) {
    Die @"
Python 3.11 or 3.12 is required, and neither was found.

The chat window (Open WebUI) does not support Python 3.13 yet -- and 3.13 is
what you get if you click the big download button on python.org. You need 3.12.

  1. Go to:  https://www.python.org/downloads/release/python-3128/
  2. Scroll to the bottom, download "Windows installer (64-bit)"
  3. IMPORTANT: on the very first screen, tick "Add python.exe to PATH"
  4. Install it, then double-click Setup Adapter.bat again

You can have 3.13 installed as well. This only needs 3.12 to exist.
"@
}
Log "python chosen: $pyExe $($pyArgs -join ' ')"

# -- GPU ---------------------------------------------------------------------
Step "Looking for your graphics card"

$gpu = $null
try { $gpu = (& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null | Select-Object -First 1) } catch { }

if ($gpu) {
    Ok "Found: $gpu"
    Ok "Interviews will transcribe on the GPU. Fast."
    $backend = "cuda"
} else {
    Warn "No NVIDIA GPU detected."
    Warn "Everything still works, but transcribing a 1-hour interview will"
    Warn "take 20-40 minutes instead of a few."
    $backend = "cpu"
}
Log "backend: $backend"

# -- Virtual environment -----------------------------------------------------
Step "Setting up Python"

if (-not (Test-Path ".venv")) {
    $c = Run -Exe $pyExe -Arguments ($pyArgs + @("-m", "venv", ".venv")) -What "create venv"
    if ($c -ne 0) { Die "Couldn't create the Python environment. See logs\setup.log." }
    Ok "Created .venv"
} else {
    Ok ".venv is already there -- reusing it"
}

$vpy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) {
    Die "The Python environment didn't build properly. Delete the .venv folder and run this again."
}
Log "venv python: $vpy"
Run -Exe $vpy -Arguments @("-c", "import sys; print(sys.version); print(sys.executable)") -What "venv version" | Out-Null

Run -Exe $vpy -Arguments @("-m", "pip", "install", "--upgrade", "pip") -What "upgrade pip" | Out-Null
Ok "Updated pip"

# -- Dependencies ------------------------------------------------------------
Step "Installing Adapter (a few minutes)"

$c = Run -Exe $vpy -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -What "requirements"
if ($c -ne 0) { Die "Install failed. The error is in logs\setup.log -- send that file." }
Ok "Core installed"

Step "Installing transcription"
$c = Run -Exe $vpy -Arguments @("-m", "pip", "install", "faster-whisper") -What "faster-whisper"
if ($c -ne 0) { Warn "Transcription failed to install. Everything else still works." }
else { Ok "Transcription installed ($backend)" }
Set-Content -Path (Join-Path $Root ".adapter_backend") -Value $backend -Encoding ascii

Step "Installing the chat window -- this is the big one, 10+ minutes"
Info "    (open-webui pulls in a lot. Let it run.)"
$c = Run -Exe $vpy -Arguments @("-m", "pip", "install", "open-webui") -What "open-webui"
if ($c -ne 0) { Die "The chat window failed to install. Send logs\setup.log -- the reason is in there." }
Ok "Chat window installed"

# -- Ollama ------------------------------------------------------------------
Step "Checking for Ollama (this is what runs the AI on your own computer)"

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    Ok "Not installed yet. Installing it now..."
    $c = Run -Exe "winget" -Arguments @("install", "--id", "Ollama.Ollama",
         "--accept-source-agreements", "--accept-package-agreements", "-h") -What "winget ollama"
    # winget changes PATH for new processes only, so pick it up by hand.
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "User")
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollama) {
        $guess = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
        if (Test-Path $guess) { $ollama = Get-Item $guess; $env:Path += ";$(Split-Path $guess)"; Log "found ollama at $guess" }
    }
}

if (-not $ollama) {
    Warn "Couldn't install Ollama automatically (winget exit code logged)."
    Warn "Download it yourself from https://ollama.com/download , install it,"
    Warn "then double-click Setup Adapter.bat again. Everything else is done,"
    Warn "so the second run will be quick."
    Log "ollama: NOT INSTALLED -- manual step required"
} else {
    Ok "Ollama is installed"
    Log "ollama: $($ollama.Source)"

    Step "Downloading the AI model -- about 9 GB, the longest part"
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 4

    $got = $null
    foreach ($m in @("qwen3:14b", "qwen2.5:14b", "qwen3:8b")) {
        Ok "Trying $m ..."
        # Pipe:$false -- ollama's progress bar is carriage-return animated and
        # fills the log with tens of thousands of partial lines if teed.
        $c = Run -Exe "ollama" -Arguments @("pull", $m) -What "pull $m" -Pipe $false
        if ($c -eq 0) { Ok "Downloaded $m"; $got = $m; break }
        Warn "$m didn't download (exit $c). Trying the next one."
    }
    if (-not $got) {
        Warn "No model downloaded. Open a Command Prompt later and run:"
        Warn "    ollama pull qwen2.5:14b"
    }
    Log "model: $got"
}

# -- Working files -----------------------------------------------------------
Step "Setting up your files"

foreach ($d in @("source\jobs", "output\resumes", "output\cover_letters", "transcripts",
                 "logs", "$env:USERPROFILE\Desktop\recordings")) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

$pairs = [ordered]@{
    "templates\master_profile.md"      = "source\master_profile.md"
    "templates\role_framing.yaml"      = "source\role_framing.yaml"
    "templates\job_filters.yaml"       = "source\job_filters.yaml"
    "templates\company_watchlist.yaml" = "source\company_watchlist.yaml"
    "templates\jd_registry.yaml"       = "source\jd_registry.yaml"
    "templates\APPLICATIONS.md"        = "APPLICATIONS.md"
}
foreach ($k in $pairs.Keys) {
    $dst = $pairs[$k]
    if (-not (Test-Path $k)) { Warn "missing template: $k"; Log "MISSING TEMPLATE $k"; continue }
    if (Test-Path $dst) { Ok "kept $dst (you already have one)" }
    else { Copy-Item $k $dst; Ok "created $dst" }
}

# -- Verify ------------------------------------------------------------------
# Checking now, while the window is still open, beats discovering it three
# steps later when nothing works and the cause is 2000 lines up the log.
Step "Checking it all actually works"

$fail = @()

$checks = [ordered]@{
    "core libraries"  = "import yaml, requests, markdown"
    "PDF rendering"   = "import weasyprint"
    "transcription"   = "import faster_whisper"
    "chat window"     = "import open_webui"
}
foreach ($name in $checks.Keys) {
    $c = Run -Exe $vpy -Arguments @("-c", $checks[$name]) -What "check: $name"
    if ($c -eq 0) { Ok "$name OK" } else { Warn "$name FAILED"; $fail += $name }
}

# Ollama answering on its port matters more than ollama.exe existing.
try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 10 -UseBasicParsing
    $models = (ConvertFrom-Json $r.Content).models
    if ($models) {
        Ok "AI model ready: $($models[0].name)"
        Log "ollama models: $(($models | ForEach-Object { $_.name }) -join ', ')"
    } else {
        Warn "Ollama is running but has no model"; $fail += "model"
    }
} catch {
    Warn "Ollama isn't answering yet. It usually starts with Windows --"
    Warn "a restart normally fixes this."
    Log "ollama api check failed: $($_.Exception.Message)"
    $fail += "ollama"
}

Log "failures: $(if ($fail.Count) { $fail -join ', ' } else { 'none' })"

# -- Done --------------------------------------------------------------------
Write-Host ""
if ($fail.Count -eq 0) {
    Write-Host "------------------------------------------------------------" -ForegroundColor Green
    Write-Host "Setup finished. Everything checks out." -ForegroundColor Green
} else {
    Write-Host "------------------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Setup finished, but these didn't pass: $($fail -join ', ')" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Try starting it anyway -- some of these fix themselves after a"
    Write-Host "restart. If not, double-click 'Share My Log.bat' and send the file."
}
Write-Host ""
Write-Host "Next: double-click " -NoNewline; Write-Host "Start Adapter.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "That opens your chat window in a browser. The first time, it asks you"
Write-Host "to make an account -- that account exists only on this computer, and"
Write-Host "the email and password are not sent anywhere."
Write-Host ""
Write-Host "Then follow local\README.md. It tells you exactly what to click."
Write-Host ""

try { Stop-Transcript | Out-Null } catch { }
Read-Host "Press Enter to close"
