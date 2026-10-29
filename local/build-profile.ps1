# Adapter -- turn your saved interview into a profile document.
#
# Don't run this directly. Double-click "Build My Profile.bat" instead.
#
# Finds the chat you downloaded, hands it to the local model, and writes
# source\master_profile.md.
#
# NOTE ON PRIVACY: logs\profile-build.log records what happened -- model,
# timings, word counts, errors -- and deliberately NOT what you said. Your
# career details stay on this machine, and stay out of any log you send us.

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_log.ps1")

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Start-AdapterLog "profile-build"

trap {
    Log "UNHANDLED $($_.Exception.Message)"
    Write-Host ""
    Write-Host "Something went wrong: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Double-click 'Share My Log.bat' and send the file."
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Build my profile" -ForegroundColor Cyan
Write-Host ""

$vpy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) {
    Write-Host "This isn't set up yet. Double-click 'Setup Adapter.bat' first." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 1
}

# -- Find the download ------------------------------------------------------
# Open WebUI's download menu writes to Downloads with a chat-derived name, so
# we go by "most recently modified export-shaped file" rather than a filename.
Step "Looking for your saved interview"

$where = @(
    (Join-Path $env:USERPROFILE "Downloads"),
    (Join-Path $env:USERPROFILE "Desktop"),
    $Root
)
$cutoff = (Get-Date).AddDays(-30)

$cands = @()
foreach ($dir in $where) {
    if (-not (Test-Path $dir)) { continue }
    $cands += Get-ChildItem -Path $dir -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Extension -in @(".txt", ".json", ".md") -and
            $_.LastWriteTime -gt $cutoff -and
            $_.Length -gt 2000 -and
            $_.Name -notlike "requirements*"
        }
}
$cands = $cands | Sort-Object LastWriteTime -Descending | Select-Object -First 8

Log "candidates found: $($cands.Count)"
foreach ($c in $cands) { Log "  cand $($c.Name)  $([math]::Round($c.Length/1KB,1))KB  $($c.LastWriteTime)" }

if ($cands.Count -eq 0) {
    Write-Host ""
    Write-Host "I couldn't find a saved chat." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "In the chat window:"
    Write-Host "  1. Click the chat's name at the top of the page"
    Write-Host "  2. Choose Download"
    Write-Host "  3. Choose 'Plain text'"
    Write-Host ""
    Write-Host "That saves it to your Downloads folder. Then run this again."
    Write-Host ""
    Write-Host "(I look for a .txt, .json or .md file over 2 KB, saved in the"
    Write-Host " last 30 days, in Downloads, Desktop, or this folder.)"
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$pick = $cands[0]
if ($cands.Count -gt 1) {
    Write-Host ""
    Write-Host "  Found these. The newest is first:"
    Write-Host ""
    for ($i = 0; $i -lt $cands.Count; $i++) {
        $c = $cands[$i]
        Write-Host ("   {0}) {1,-42} {2,7} KB   {3}" -f ($i + 1), $c.Name,
                    [math]::Round($c.Length / 1KB, 0), $c.LastWriteTime.ToString("MMM d HH:mm"))
    }
    Write-Host ""
    $ans = Read-Host "Which one? (Enter for 1)"
    if ($ans -match '^\d+$' -and [int]$ans -ge 1 -and [int]$ans -le $cands.Count) {
        $pick = $cands[[int]$ans - 1]
    }
}

Ok "Using: $($pick.FullName)"
Log "chosen: $($pick.Name) ($($pick.Length) bytes)"

# -- Run it -----------------------------------------------------------------
Step "Writing your profile"
Write-Host "    This takes a few minutes. The GPU does the work."
Write-Host ""

# Pipe:$false matters here. Run tees stdout into the log, and this script's
# stdout is the review checklist -- real job titles, real numbers, the user's
# actual career. That must not land in a file they email to a stranger.
# extract_profile.py --log writes its own technical-only log instead.
$c = Run -Exe $vpy -Arguments @((Join-Path $Root "local\extract_profile.py"), $pick.FullName, "--log") -Pipe $false
Log "extract exit: $c"

Write-Host ""
if ($c -ne 0) {
    Write-Host "That didn't finish. The technical details are in" -ForegroundColor Red
    Write-Host "logs\profile-build.log -- double-click 'Share My Log.bat' and send it."
} else {
    Write-Host "------------------------------------------------------------" -ForegroundColor Green
    Write-Host "Read the list above before you use this anywhere." -ForegroundColor Green
    Write-Host ""
    Write-Host "The local model gets small things wrong -- a job title you never"
    Write-Host "said, a city it assumed, a number it dropped. That's what the list"
    Write-Host "is for. Open the file and fix them now, while it's fresh:"
    Write-Host ""
    Write-Host "    source\master_profile.md" -ForegroundColor Cyan
    Write-Host ""
    $open = Read-Host "Open it now? (Y/n)"
    if ($open -ne "n" -and $open -ne "N") {
        Start-Process notepad.exe (Join-Path $Root "source\master_profile.md")
    }
}
Write-Host ""
Read-Host "Press Enter to close"
