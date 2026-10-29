# Shared logging for the Windows scripts. Dot-sourced by them, not run directly.
#
# Why this file exists: the person running these scripts is probably not the
# person who can fix them. Everything printed to the screen is also written to
# logs\<name>.log with timestamps and exit codes, so a failed install can be
# diagnosed from the log alone, by someone who isn't sitting at the machine.
#
# What deliberately does NOT go in the logs: anything from the career
# interview, and anything out of master_profile.md. Those logs get emailed to
# a stranger. See collect-logs.ps1.

function Start-AdapterLog {
    param([Parameter(Mandatory=$true)][string]$Name)

    $dir = Join-Path $PSScriptRoot "..\logs"
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $global:AdapterLogName = $Name
    $global:AdapterLog = (Join-Path $dir "$Name.log")

    # Keep the previous run as .prev. A second attempt is usually made
    # immediately after a failure, and it would otherwise erase the evidence
    # from the attempt we actually want to see.
    if (Test-Path $global:AdapterLog) {
        Move-Item -Force -Path $global:AdapterLog -Destination "$($global:AdapterLog).prev" -ErrorAction SilentlyContinue
    }
    Set-Content -Path $global:AdapterLog -Value "" -Encoding utf8 -ErrorAction SilentlyContinue

    Log "=== $Name === $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
    Log "script: $($MyInvocation.ScriptName)"
}

function Log {
    param([string]$Text)
    if (-not $global:AdapterLog) { return }
    try {
        Add-Content -Path $global:AdapterLog -Value ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Text) -Encoding utf8
    } catch { }
}

# Screen + log. The screen gets the friendly version; the log gets both.
function Step { param([string]$m) Write-Host ""; Write-Host "==> $m" -ForegroundColor Green; Log "STEP $m" }
function Ok   { param([string]$m) Write-Host "    $m" -ForegroundColor Gray;              Log "  ok  $m" }
function Warn { param([string]$m) Write-Host "  ! $m" -ForegroundColor Yellow;            Log "  WARN $m" }
function Info { param([string]$m) Write-Host $m }

function Die {
    param([string]$m)
    Log "DIE $m"
    Write-Host ""
    Write-Host "STOPPED: $m" -ForegroundColor Red
    Write-Host ""
    Write-Host "This was written to:" -ForegroundColor Cyan
    Write-Host "  $global:AdapterLog"
    Write-Host ""
    Write-Host "If you're stuck, double-click 'Share My Log.bat' and send the file"
    Write-Host "it makes. It has everything needed to work out what happened."
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

# Run an external command. Output goes to the screen AND the log, and the exit
# code is recorded either way. Returns the exit code; never throws.
#
# ShowProgress:$false for commands that draw progress bars with carriage
# returns (ollama pull) -- piping those produces megabytes of unreadable log.
function Run {
    param(
        [Parameter(Mandatory=$true)][string]$Exe,
        [string[]]$Arguments = @(),
        [string]$What = "",
        [bool]$Pipe = $true
    )
    Log "RUN $Exe $($Arguments -join ' ')"
    $global:LASTEXITCODE = 0
    try {
        if ($Pipe) {
            # Out-Host is load-bearing. Tee-Object passes its input THROUGH,
            # so without it every line of pip's output becomes part of this
            # function's return value and the caller's "$c -ne 0" compares
            # against an array instead of the exit code.
            & $Exe @Arguments 2>&1 | Tee-Object -FilePath $global:AdapterLog -Append | Out-Host
        } else {
            Log "  (output shown on screen only -- progress bar)"
            & $Exe @Arguments 2>&1 | Out-Host
        }
    } catch {
        Log "  THREW $($_.Exception.Message)"
        return 1
    }
    $code = $LASTEXITCODE
    if ($null -eq $code) { $code = 0 }
    Log "EXIT $code $What"
    return $code
}

# Everything about this machine that could plausibly explain a failure.
# Called at the start of setup and again by Share My Log.bat, so the bundle is
# useful even when setup never got far enough to log anything.
function Write-Environment {
    Log "---------------- machine ----------------"
    try {
        Log "windows: $((Get-CimInstance Win32_OperatingSystem).Caption) build $((Get-CimInstance Win32_OperatingSystem).BuildNumber)"
        Log "ram_gb: $([math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1))"
        Log "cpu: $((Get-CimInstance Win32_Processor | Select-Object -First 1).Name)"
    } catch { Log "machine info failed: $($_.Exception.Message)" }

    Log "powershell: $($PSVersionTable.PSVersion) ($($PSVersionTable.PSEdition))"
    Log "is_admin: $([bool](([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)))"
    Log "repo: $((Resolve-Path (Join-Path $PSScriptRoot '..')).Path)"

    try {
        $d = Get-PSDrive -Name ((Get-Location).Drive.Name) -ErrorAction Stop
        Log "disk_free_gb: $([math]::Round($d.Free / 1GB, 1))"
    } catch { Log "disk check failed" }

    Log "---------------- gpu ----------------"
    $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($smi) {
        try {
            $g = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>&1
            Log "nvidia-smi: $g"
        } catch { Log "nvidia-smi present but failed: $($_.Exception.Message)" }
    } else {
        Log "nvidia-smi: not on PATH"
        try {
            foreach ($v in (Get-CimInstance Win32_VideoController)) {
                Log "video_controller: $($v.Name) ($([math]::Round($v.AdapterRAM / 1GB, 1)) GB reported)"
            }
        } catch { }
    }

    Log "---------------- python ----------------"
    foreach ($cmd in @("py", "python", "python3")) {
        $c = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($c) { Log "$cmd -> $($c.Source)" } else { Log "$cmd -> not found" }
    }
    try {
        $list = & py -0p 2>&1
        Log "py -0p: $($list -join ' | ')"
    } catch { Log "py -0p: unavailable" }

    Log "---------------- tools ----------------"
    foreach ($cmd in @("ollama", "winget", "git", "curl")) {
        $c = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($c) { Log "$cmd -> $($c.Source)" } else { Log "$cmd -> not found" }
    }
    Log "---------------- end ----------------"
}
