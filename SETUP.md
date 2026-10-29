# Setup

Adapter has no interface of its own. It is a set of files and scripts that an AI
assistant reads and runs on your behalf, in a terminal, on your machine.
**The assistant is the UI.**

Budget about ten minutes for setup. The career interview that follows takes
longer, and you can spread it over several sittings.

---

## 1. Requirements

- **Python 3.10+**
- **An AI assistant with filesystem and shell access.** Built and tested with
  [Claude Code](https://claude.com/claude-code). Anything that can read files
  and run commands in a directory works — the skills are markdown instructions,
  not a proprietary format.
- **A GPU helps but isn't required.** Transcription is the only part that cares.

## 2. Install

```bash
git clone <your-fork-url> adapter
cd adapter
./setup.sh
```

The script detects your hardware, installs the right transcription backend,
copies the templates into place, checks that nothing personal is tracked by git,
and verifies the result. It is safe to re-run — it never overwrites files you
already have.

### What it picks, and what that means

| Your hardware | Backend | Speed |
|---|---|---|
| Apple Silicon (M1–M4) | `mlx-whisper`, Apple GPU | Fast — roughly 10x real time |
| NVIDIA GPU | `faster-whisper`, CUDA | Fast |
| Anything else | `faster-whisper`, CPU | 5–15x slower. A one-hour interview takes 20–40 minutes. |

CPU is a real option, not a broken one. Everything other than transcription runs
the same on all three.

Override the choice any time:

```bash
python3 source/transcribe.py recording.m4a out.txt --backend cpu
```

**If weasyprint fails to import**, the system libraries it needs are missing:

```bash
brew install pango gdk-pixbuf libffi                       # macOS
sudo apt install libpango-1.0-0 libpangoft2-1.0-0          # Debian/Ubuntu
```

## 3. Start your assistant

```bash
source .venv/bin/activate
claude
```

Then say:

> **I'm new here. Walk me through setting this up.**

That's the whole integration. Claude Code reads `CLAUDE.md` automatically, finds
the profile still empty, and starts the career interview.

**Using something other than Claude Code?** Paste
[`BOOTSTRAP.md`](BOOTSTRAP.md) into the conversation first. It does by hand what
Claude Code does automatically — points the assistant at the rules and the
procedure. Nothing here depends on a specific vendor.

---

## 4. What the script laid out

Your working files are copies, so a `git pull` never overwrites your data:

```
source/master_profile.md        your career, the source of everything
source/role_framing.yaml        which titles to chase and which to avoid
source/job_filters.yaml         freshness, location, comp floor, exclusions
source/company_watchlist.yaml   companies to watch directly — starts empty
source/jd_registry.yaml         joins applications to postings and documents
APPLICATIONS.md                 the tracker the dashboard parses
```

All of them are gitignored, along with `transcripts/` and `output/`. The setup
script checks this, but it's worth knowing why: these files contain your salary
expectations, your private rankings of employers, and transcripts with other
people's voices in them.

Optional — a filename prefix for generated documents:

```bash
export ADAPTER_DOC_PREFIX="Smith_"    # -> output/resumes/Smith_Acme_Role.pdf
```

## 5. Transcription

Models download on first use and cache locally.

```bash
python3 source/transcribe.py <audio> <output.txt>
```

| Flag | Default | Notes |
|---|---|---|
| `--model` | `medium` | `turbo` is faster *and* usually more accurate. `tiny`…`large` also available. |
| `--language` | `en` | Pinned on purpose — see below. |
| `--backend` | auto | `mlx`, `cuda` or `cpu`. |

Drop recordings in `~/Desktop/recordings` and the `transcribe` skill finds them
without being told where to look.

**Language is pinned deliberately.** Whisper auto-detects from the opening
seconds of audio, and a quiet or noisy start can make it guess wrong. When that
happens it doesn't just mislabel the output — it translates the entire file into
the wrong language and falls into repetition loops. Pass `--language none` only
if you actually want detection.

Two files are written: plain prose, and `.timed.txt` with `[hh:mm:ss]` markers
so a disputed line can be checked against the recording.

## 6. Optional: Gmail and Calendar

Only needed if you want the assistant reading recruiter email and scheduling
directly. **Everything else works without it.**

Create an OAuth client in Google Cloud Console (Desktop app type), enable the
Gmail and Calendar APIs, download the client JSON to
`source/gmail_credentials.json`, then:

```bash
python3 source/google_auth.py
```

Scopes are read-only by design; the code cannot exceed them.

> ⚠️ **Keep the OAuth app in "Testing" status and Google expires your refresh
> token every 7 days.** When that happens the auth helper tries to open an
> interactive browser flow — which, called from inside a long-running tool,
> blocks silently until it times out. If email calls start hanging, re-run
> `python3 source/google_auth.py` from a terminal. Publishing the OAuth app
> stops the weekly expiry.

## 7. Verify by hand

`setup.sh` already does this, but if you want to check again:

```bash
python3 source/job_scout.py --verify      # watchlist slugs resolve
python3 source/pipeline.py                # dashboard renders (empty is fine)
python3 source/md_to_pdf.py templates/master_profile.md /tmp/test.pdf
```

---

## What stays on your machine

Transcription is local on every backend — audio never leaves the device. That's
the point, given the recordings are conversations with real people.

The assistant itself is a hosted model, so **anything you paste into the
conversation goes to that provider.** Your profile, your transcripts and your
application notes are as private as your assistant's terms say they are. Worth
knowing before you paste a transcript of someone else's voice.
