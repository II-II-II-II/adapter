# Adapter -- bundle everything needed to diagnose a problem into one file.
#
# Don't run this directly. Double-click "Share My Log.bat" instead.
#
# Makes a single text file on your Desktop and opens it. Send that file to
# whoever gave you this, or attach it to a GitHub issue.
#
# WHAT GOES IN IT
#   Your Windows version, graphics card, Python versions, which packages
#   installed and which failed, exit codes, and every error message from the
#   scripts. Your Windows username appears in file paths.
#
# WHAT DOES NOT GO IN IT
#   Nothing from your career interview. Nothing from your profile, resumes,
#   applications or transcripts. The scripts never write that to a log, and
#   this reports only whether those files exist and how long they are.
#   Read the file before sending it -- it's plain text and that's the point.

$ErrorActionPreference = "Continue"

. (Join-Path $PSScriptRoot "_log.ps1")

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Start-AdapterLog "diagnostic"

Write-Host "Collecting your log" -ForegroundColor Cyan
Write-Host ""

# -- Fresh snapshot of the machine ------------------------------------------
# Deliberately re-run rather than trusting setup's copy: this has to be useful
# even when setup failed so early that it logged nothing at all.
Step "Checking this computer"
Write-Environment
Ok "done"

# -- Live state -------------------------------------------------------------
Step "Checking what's installed"

$vpy = Join-Path $Root ".venv\Scripts\python.exe"
Log "---------------- install state ----------------"
Log "venv python exists: $(Test-Path $vpy)"

if (Test-Path $vpy) {
    Run -Exe $vpy -Arguments @("-c", "import sys; print(sys.version)") -What "venv version" | Out-Null

    $mods = @("yaml", "requests", "markdown", "weasyprint", "faster_whisper", "open_webui")
    foreach ($m in $mods) {
        $c = Run -Exe $vpy -Arguments @("-c", "import $m, sys; print('$m', getattr($m, '__version__', 'no version attr'))") -What "import $m"
        if ($c -eq 0) { Ok "$m OK" } else { Warn "$m missing or broken" }
    }

    Log "---------------- pip freeze ----------------"
    Run -Exe $vpy -Arguments @("-m", "pip", "freeze") -What "pip freeze" | Out-Null
} else {
    Warn "Python environment not built -- setup didn't finish"
}

Step "Checking the AI"
try {
    $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 8 -UseBasicParsing
    $models = (ConvertFrom-Json $r.Content).models
    if ($models) {
        foreach ($m in $models) { Log "model: $($m.name)  $([math]::Round($m.size/1GB,2)) GB" }
        Ok "Ollama answering, $($models.Count) model(s)"
    } else { Warn "Ollama answering but no models downloaded"; Log "ollama: 0 models" }
} catch {
    Warn "Ollama not answering on port 11434"
    Log "ollama api: FAILED $($_.Exception.Message)"
}

try {
    $null = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5 -UseBasicParsing
    Ok "Chat window is running"; Log "openwebui port 8080: serving"
} catch {
    Ok "Chat window not currently running (fine if you closed it)"
    Log "openwebui port 8080: not serving"
}

# -- File layout: existence and size only, never content --------------------
Step "Checking your files"
Log "---------------- file layout ----------------"
$watch = @(
    "source\master_profile.md", "source\role_framing.yaml", "source\job_filters.yaml",
    "source\company_watchlist.yaml", "source\jd_registry.yaml", "APPLICATIONS.md",
    ".adapter_backend", "local\SYSTEM_PROMPT.md", "requirements.txt"
)
foreach ($f in $watch) {
    if (Test-Path $f) {
        $fi = Get-Item $f
        $lines = 0
        try { $lines = (Get-Content $f -ErrorAction Stop | Measure-Object -Line).Lines } catch { }
        # Lines and bytes only. The contents are the user's career history.
        Log "present: $f  ($lines lines, $($fi.Length) bytes, modified $($fi.LastWriteTime))"
    } else {
        Log "MISSING: $f"
    }
}
if (Test-Path ".adapter_backend") { Log "backend: $(Get-Content '.adapter_backend' -Raw)" }
Ok "done"

# -- Bundle -----------------------------------------------------------------
Step "Building the file to send"

$logDir = Join-Path $Root "logs"
$stamp = Get-Date -Format "yyyy-MM-dd-HHmm"
$out = Join-Path ([Environment]::GetFolderPath("Desktop")) "adapter-log-$stamp.txt"

$header = @"
================================================================
 ADAPTER DIAGNOSTIC LOG
 generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
================================================================

This contains setup and startup logs, this computer's specs, and which
packages installed. It does NOT contain anything from the career
interview or the profile document.

Sections below, newest activity usually last.

"@
Set-Content -Path $out -Value $header -Encoding utf8

$files = Get-ChildItem -Path $logDir -File -ErrorAction SilentlyContinue |
         Where-Object { $_.Extension -in @(".log", ".prev") -or $_.Name -like "*.log.prev" } |
         Sort-Object Name

$MAX = 3000   # a failed pip install can write a very long transcript

foreach ($f in $files) {
    Add-Content -Path $out -Value "`r`n`r`n================ $($f.Name) ================" -Encoding utf8
    Add-Content -Path $out -Value "($([math]::Round($f.Length/1KB,1)) KB, modified $($f.LastWriteTime))`r`n" -Encoding utf8
    try {
        $content = Get-Content $f.FullName -ErrorAction Stop
        if ($content.Count -gt $MAX) {
            Add-Content -Path $out -Value "[... first $($content.Count - $MAX) lines trimmed; full file is logs\$($f.Name) ...]`r`n" -Encoding utf8
            $content = $content[-$MAX..-1]
        }
        Add-Content -Path $out -Value $content -Encoding utf8
    } catch {
        Add-Content -Path $out -Value "[couldn't read this log: $($_.Exception.Message)]" -Encoding utf8
    }
}

Add-Content -Path $out -Value "`r`n`r`n================ end ================" -Encoding utf8

$size = [math]::Round((Get-Item $out).Length / 1KB, 1)

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Green
Write-Host "Made this file on your Desktop:" -ForegroundColor Green
Write-Host ""
Write-Host "    adapter-log-$stamp.txt   ($size KB)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Email it, or drop it into a GitHub issue. It's plain text --"
Write-Host "open it and read it first if you want to."
Write-Host ""
Write-Host "It has: your Windows version, graphics card, Python versions, which"
Write-Host "packages installed, and every error the scripts hit."
Write-Host ""
Write-Host "It does NOT have: anything you said in the interview, and nothing"
Write-Host "out of your profile, resumes or applications."
Write-Host ""
Write-Host "Also worth saying out loud, in your own words: what you clicked, what"
Write-Host "you expected, and what happened instead. That's usually the fastest"
Write-Host "clue in the whole bundle."
Write-Host ""

Log "bundle written: $out ($size KB, $($files.Count) logs)"

$open = Read-Host "Open it now? (Y/n)"
if ($open -ne "n" -and $open -ne "N") { Start-Process notepad.exe $out }
Start-Process explorer.exe ("/select,`"$out`"")

Read-Host "Press Enter to close"
