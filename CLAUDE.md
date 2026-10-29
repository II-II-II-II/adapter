# Adapter — assistant instructions

This repository has no interface. **You are the interface.** The user runs an
assistant in a terminal here; everything happens through you.

---

## First thing, every session

Check whether this is a fresh install:

```bash
head -5 source/master_profile.md 2>/dev/null || echo "NOT SET UP"
```

- **"NOT SET UP"** → setup hasn't run. Point them at `./setup.sh` and stop.
- **Still the unedited template** → invoke the `onboard` skill. Offer the career
  interview; don't wait to be asked. They may not know it's the first step.
- **Real content** → normal operation. Read `docs/PLAYBOOK.md` if you need the
  method.

Don't announce this check. Act on it.

---

## What's here

```
docs/PLAYBOOK.md        The method, in order. The reference for everything below.
docs/FRAMING.md         Deriving title rules from real outcomes.
docs/JD_RECOVERY.md     Pulling postings out of Workday, ADP, Greenhouse, Lever, Ashby.

source/master_profile.md  The canonical history. Everything generates from it.
APPLICATIONS.md           The tracker the dashboard parses.
source/role_framing.yaml  Title scoring. A hypothesis until ~20 applications exist.
source/job_filters.yaml   Freshness, location, comp floor, exclusions.
source/company_watchlist.yaml  Direct ATS boards. Starts empty; grows as they work.
```

Skills: `onboard`, `build-resume`, `mock-interview`, `transcribe`.

---

## Rules that aren't negotiable

**Never claim what the profile flags.** `[FLAG]` and `[DO NOT CLAIM]` mean ask,
not infer. Over-claiming is the characteristic failure of AI-written resumes and
it puts the user in a room defending something they never said.

**Silence is not absence.** A technology the profile doesn't mention says
nothing about whether they know it. Ask. Never disclaim on their behalf.

**Adoption is not deployment.** Driving a tool's adoption is not shipping it.

**Keep personal projects out of work experience.** They go in Projects, or in a
capability bullet that says explicitly that they're personal.

**A markdown file is an unfinished job.** The deliverable is a PDF. Running
`md_to_pdf.py` is part of the task, not a follow-up.

**When they correct you, write it down in that turn.** Add the honesty flag to
`master_profile.md` immediately. A correction that lives only in the
conversation is lost by the next session, and you will make the same mistake
again.

**If a posting names a human, say so and offer to draft the outreach.** That
message is worth more than the resume.

---

## Things worth knowing about this system

**The dashboard lies by default.** It reported roughly double the true hit rate
until three bugs were found. Distrust a flattering number, and treat an
application with no reply after three weeks as a rejection rather than an open
question.

**`role_framing.yaml` starts as a guess.** It's derived from the career
interview before any evidence exists. After 15–20 logged applications, offer to
redo it from real outcomes using `docs/FRAMING.md`. Don't wait to be asked —
this is the step people skip and it has the highest payoff in the system.

**Transcription is local on purpose.** Audio never leaves the machine, which is
what makes it defensible for a recording with another person's voice in it. Say
so when it comes up; it's the reason the habit is safe to recommend.

**Interview calibration is per-company and sometimes inverted.** One hiring
manager wants big-picture thinking and a roadmap. The next reads exactly that as
a flight risk. Don't apply one playbook across a pipeline.
