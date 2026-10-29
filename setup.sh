#!/usr/bin/env bash
#
# Adapter setup. Detects your hardware, installs the right transcription
# backend, and lays out your working files.
#
#   ./setup.sh
#
set -euo pipefail

cd "$(dirname "$0")"

bold=$'\033[1m'; dim=$'\033[2m'; green=$'\033[32m'; yellow=$'\033[33m'; off=$'\033[0m'
say()  { printf '%s\n' "$*"; }
step() { printf '\n%s==>%s %s%s\n' "$green" "$off" "$bold" "$*"; printf '%s' "$off"; }
warn() { printf '%s!%s  %s\n' "$yellow" "$off" "$*"; }

# ── 1. Python ────────────────────────────────────────────────────────────────
step "Checking Python"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null 2>&1; then
        v=$("$c" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo 0.0)
        if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
            PY="$c"; say "  Python $v  ($(command -v "$c"))"; break
        fi
    fi
done
[ -n "$PY" ] || { warn "Python 3.10+ required and not found. Install it, then re-run."; exit 1; }

# ── 2. Hardware → transcription backend ──────────────────────────────────────
step "Detecting hardware"

OS=$(uname -s)
ARCH=$(uname -m)
BACKEND=""

if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    BACKEND="mlx"
    say "  Apple Silicon detected."
    say "  ${dim}Transcription runs on the Apple GPU via MLX. Fast.${off}"
elif command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
    BACKEND="cuda"
    gpu=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || echo "NVIDIA GPU")
    say "  NVIDIA GPU detected: $gpu"
    say "  ${dim}Transcription runs on CUDA via faster-whisper. Fast.${off}"
else
    BACKEND="cpu"
    say "  No supported GPU found — falling back to CPU."
    warn "CPU transcription is roughly 5–15x slower than GPU."
    warn "A one-hour interview may take 20–40 minutes. Everything else is unaffected."
fi

# ── 3. Virtual environment ───────────────────────────────────────────────────
step "Creating virtual environment"

if [ -d .venv ]; then
    say "  .venv already exists — reusing it."
else
    "$PY" -m venv .venv
    say "  Created .venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip

# ── 4. Dependencies ──────────────────────────────────────────────────────────
step "Installing dependencies"
say "  ${dim}This takes a few minutes the first time.${off}"

python -m pip install --quiet -r requirements.txt

case "$BACKEND" in
    mlx)
        python -m pip install --quiet "mlx-whisper>=0.4.0"
        say "  Installed mlx-whisper (Apple GPU)"
        ;;
    cuda)
        python -m pip install --quiet "faster-whisper>=1.0.0"
        say "  Installed faster-whisper (CUDA)"
        say "  ${dim}Needs NVIDIA cuDNN/cuBLAS. If transcription errors on load,${off}"
        say "  ${dim}see: https://github.com/SYSTRAN/faster-whisper#gpu${off}"
        ;;
    cpu)
        python -m pip install --quiet "faster-whisper>=1.0.0"
        say "  Installed faster-whisper (CPU)"
        ;;
esac

printf '%s\n' "$BACKEND" > .adapter_backend

# ── 5. Working files ─────────────────────────────────────────────────────────
step "Laying out your working copy"

mkdir -p source/jobs output/resumes output/cover_letters transcripts ~/Desktop/recordings

copy_template() {
    src="templates/$1"; dst="$2"
    if [ -e "$dst" ]; then
        say "  ${dim}kept   $dst (already exists)${off}"
    else
        cp "$src" "$dst"; say "  copied $dst"
    fi
}

copy_template master_profile.md     source/master_profile.md
copy_template role_framing.yaml     source/role_framing.yaml
copy_template job_filters.yaml      source/job_filters.yaml
copy_template company_watchlist.yaml source/company_watchlist.yaml
copy_template jd_registry.yaml      source/jd_registry.yaml
copy_template APPLICATIONS.md       APPLICATIONS.md

# ── 6. Privacy check ─────────────────────────────────────────────────────────
step "Checking nothing personal is tracked by git"

if [ -d .git ]; then
    # git ls-files, not git status: status only reports *modified* tracked
    # files, so a committed-but-unchanged profile would pass silently.
    leaked=$(git ls-files 2>/dev/null \
        | grep -E '^(source/(master_profile|role_framing|job_filters|company_watchlist|jd_registry)|APPLICATIONS\.md|INTERVIEWS\.md|transcripts/|output/)' || true)
    if [ -n "$leaked" ]; then
        warn "These personal files are tracked by git:"
        printf '%s\n' "$leaked"
        warn "Fix with:  git rm --cached <file>   before you push anywhere."
    else
        say "  Clean. Your profile, tracker and transcripts are all gitignored."
    fi
else
    say "  ${dim}Not a git repo — nothing to check.${off}"
fi

# ── 7. Verify ────────────────────────────────────────────────────────────────
step "Verifying"

ok=true
python -c 'import yaml, requests, markdown' 2>/dev/null \
    && say "  core imports OK" || { warn "core imports FAILED"; ok=false; }

python -c 'import weasyprint' 2>/dev/null \
    && say "  PDF rendering OK" \
    || { warn "weasyprint failed to import — PDF output won't work."
         warn "macOS:  brew install pango gdk-pixbuf libffi"
         warn "Debian: sudo apt install libpango-1.0-0 libpangoft2-1.0-0"; ok=false; }

case "$BACKEND" in
    mlx)  python -c 'import mlx_whisper'     2>/dev/null && say "  mlx-whisper OK"     || { warn "mlx-whisper import FAILED"; ok=false; } ;;
    *)    python -c 'import faster_whisper'  2>/dev/null && say "  faster-whisper OK"  || { warn "faster-whisper import FAILED"; ok=false; } ;;
esac

python source/pipeline.py >/dev/null 2>&1 \
    && say "  dashboard renders" || say "  ${dim}dashboard empty (expected on a fresh install)${off}"

# ── 8. What to do next ───────────────────────────────────────────────────────
printf '\n'
if $ok; then
    printf '%s─────────────────────────────────────────────────────────────%s\n' "$green" "$off"
    printf '%sSetup complete.%s\n\n' "$bold" "$off"
else
    printf '%s─────────────────────────────────────────────────────────────%s\n' "$yellow" "$off"
    printf '%sSetup finished with warnings above.%s You can still start.\n\n' "$bold" "$off"
fi

say "Adapter has no interface of its own — an AI assistant reads these files"
say "and runs the commands. That's the whole design."
printf '\n'
say "${bold}Start your assistant in this directory:${off}"
say "    ${dim}source .venv/bin/activate${off}"
say "    ${dim}claude${off}            ${dim}# or whatever assistant you use${off}"
printf '\n'
say "${bold}Then say exactly this:${off}"
printf '\n'
say "    ${bold}I'm new here. Walk me through setting this up.${off}"
printf '\n'
say "${dim}Not using Claude Code? Paste BOOTSTRAP.md into your assistant first.${off}"
printf '\n'
