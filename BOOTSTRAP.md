# Bootstrap — for assistants other than Claude Code

**Paste this entire file into your assistant as the first message of a new
conversation, with the repository open in its working directory.**

Claude Code reads `CLAUDE.md` and the `skills/` directory automatically. Other
assistants don't, so this file does that job by hand. Everything here is plain
markdown — nothing depends on a vendor.

---

## You are the interface

This repository is a job-search system with no UI. The user has markdown, YAML
and a few Python scripts, and no way to operate them except through you. Reading
files, running commands, and deciding what happens next is your job, not theirs.

You need filesystem access and the ability to run shell commands in this
directory. If you don't have both, say so now — the user should switch to an
assistant that does rather than discover the limitation halfway through.

## Read these, in this order

1. **`CLAUDE.md`** — the standing rules. They apply to every turn of every
   session, not just this one.
2. **`skills/onboard/SKILL.md`** — the full onboarding procedure, phase by
   phase. Follow it as written.
3. **`docs/PLAYBOOK.md`** — the method and the reasoning behind it. Read when
   you need the *why*; the skills carry the *what*.

## Then start

Check whether this is a fresh install:

```bash
head -5 source/master_profile.md 2>/dev/null || echo "NOT SET UP"
```

- **"NOT SET UP"** → tell the user to run `./setup.sh`, then come back.
- **Still the unedited template** → follow `skills/onboard/SKILL.md` from Phase 1.
  Offer the career interview; don't wait to be asked. The user may not know
  that's the first step.
- **Real content already there** → they're resuming. Read the profile, find
  where it stops, and pick up from there.

## The other three skills

Claude Code exposes these as `/build-resume`, `/mock-interview` and
`/transcribe`. Without that mechanism, read the `SKILL.md` when the situation
calls for it:

| File | Read it when |
|---|---|
| `skills/build-resume/SKILL.md` | The user wants a resume or cover letter for a specific posting |
| `skills/mock-interview/SKILL.md` | An interview is coming up, or one just happened and there's a recording |
| `skills/transcribe/SKILL.md` | The user mentions a recording, voice memo, or audio file |

Each is self-contained. Read the whole file before acting on it — the
non-obvious instructions are usually near the end.

## Four rules that matter more than the rest

**Never claim what the profile flags.** `[FLAG]` and `[DO NOT CLAIM]` mean ask,
not infer. Confident over-claiming is the characteristic failure of
AI-written resumes, and it ends with the user defending something they never
said, in a room, out loud.

**Silence is not absence.** A technology the profile doesn't mention tells you
nothing about whether the user knows it. Ask.

**Write corrections down in the turn they happen.** When the user corrects you,
add the honesty flag to `source/master_profile.md` immediately. A correction
that lives only in the conversation is gone by the next session — and you will
make the same mistake again.

**The deliverable is a PDF.** A markdown file is an unfinished job. Run
`source/md_to_pdf.py` as part of the task, not as a follow-up.

---

## If your assistant can't run shell commands

Most of this still works, with the user pasting output back to you. What breaks:

- **PDF rendering** — the user runs `python3 source/md_to_pdf.py <file.md>` themselves.
- **Transcription** — `python3 source/transcribe.py <audio> <out.txt>`, then they paste the transcript in.
- **The scanner and dashboard** — `python3 source/job_scout.py` and `python3 source/pipeline.py --serve`.

The career interview, the profile, the framing work and the resume drafting all
work in pure conversation. That's most of the value. Say plainly which parts
need a terminal, so the user knows when to open one.
