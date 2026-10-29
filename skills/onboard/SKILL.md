---
name: onboard
description: Set up a new Adapter user from nothing — run the career interview, build their master profile, work out which job titles they should actually target, and get them to a first finished resume. Use on a fresh install, when source/master_profile.md is still the unedited template, or when the user says they're new, wants to get started, has no resume, or doesn't know what kind of job to apply for.
---

# Onboarding

You are the interface. The user has just cloned a repository of markdown and
Python and has no idea what to do with it. Everything that follows is your job,
not theirs.

**Assume the hardest case, because it's the common one:** no current resume, no
clear target job, and a career that doesn't summarise neatly. Someone with a
polished resume and a specific title in mind is the easy path through this same
procedure.

---

## Before you start

Check what state they're in:

```bash
ls source/master_profile.md APPLICATIONS.md 2>/dev/null
head -5 source/master_profile.md 2>/dev/null
```

- **Files missing** → setup didn't complete. Walk them through `./setup.sh` first.
- **Profile is still the template** (has the placeholder headings, no real content) → start at Phase 1.
- **Profile has real content** → they're resuming. Jump to **Resuming an interview**.

---

# Phase 1 — Frame it, then get out of the way

Say roughly this, in your own words, and keep it to a few lines:

> The next part is a conversation about your career. I'll ask questions and
> write the profile as we go — you don't have to prepare anything or have a
> resume. We can do it in one sitting or spread it over a few; I'll save as we
> go either way.

Then ask **one** question to open:

> Where did you start? Not your current job — the first one that's relevant to
> where you're trying to go.

**Do not** present a list of phases, a progress bar, or an agenda. The user
agreed to a conversation. Give them one.

---

# Phase 2 — The career interview

The single highest-leverage hour in this system. Everything downstream — every
resume, every framing decision, every interview answer — generates from what
you capture here.

## Run it chronologically, oldest first

People narrate forward and compress backward. Starting at the present gets you
the resume they already have in their head; starting at the beginning gets you
the material they'd never think to include.

## Four questions per role

For every job, in this order:

1. **What did you own?** — the thing that was yours, where you'd be the one called.
2. **What broke?** — the outage, the failed launch, the thing that went wrong.
3. **What did you build?** — made to exist, not maintained.
4. **What did you decide alone?** — judgment with nobody to escalate to.

Then follow wherever the energy goes. A flat answer to all four usually means
the role was unremarkable; move on quickly rather than mining it.

## Probe for what people leave out

These are the best interview material in anyone's career and nobody volunteers
them, because they don't feel like achievements:

- The thing that broke at 2am, and what it turned out to be
- A redesign forced by something outside their control — a supply shock, a
  vendor collapse, a regulation
- A deadline they shouldn't have hit, and how
- Something they argued for and lost, and whether they were right
- The system everyone hated that they had to keep alive anyway

Ask directly. *"What's the worst night you had in that job?"* gets better
material than *"tell me about a challenge."*

## Chase every number

"Large," "a lot," "high traffic" and "a big team" are not numbers. Ask: how
many users, how many sites, how many devices, what was the budget, what was the
uptime, how many people reported to you, how long did it run.

If they genuinely don't remember, write `[FLAG: number not recalled]` rather
than a guess. A guess becomes a claim they have to defend in a room.

## Write as you go, and flag every correction

Append to `source/master_profile.md` after **each role**, not at the end. Two
reasons: the user can stop at any point without losing the session, and they can
see the document forming, which makes them correct it.

**When the user pushes back, write the flag in that same turn.** A correction
that lives only in the conversation is gone by the next session. The honesty
markers are defined at the top of `master_profile.md`:

| Marker | Means |
|---|---|
| `[RESUME-SAFE]` | Verified, claim it freely |
| `[PERSONAL]` | Real, but personal project — never employer work |
| `[DEMO]` | Built to learn; never present as production |
| `[STALE]` | True once; currency unverified |
| `[FLAG]` | Unresolved — ask before using |
| `[DO NOT CLAIM]` | Explicitly corrected. Never write this again. |

Two rules you will need repeatedly:

- **Silence is not absence.** The profile not mentioning a technology says
  nothing about whether they know it. Ask; never disclaim on their behalf.
- **Adoption is not deployment.** Driving a tool's adoption across a company is
  not the same as having shipped it. Keep that line sharp.

## Resuming an interview

Read the profile, find the last role covered, and open with what you already
know rather than making them repeat themselves:

> Last time we got through [role] at [company]. Want to pick up at [next role]?

---

# Phase 3 — Title triangulation

**Do not skip this, and do not do it silently.** For a user who doesn't know
what to apply for, this is the most valuable thing the system does — and the
only part that has to happen *before* they send applications rather than after.

## Do the arithmetic they can't do for themselves

Tally years by **domain**, not by job title. Job titles drift, get inflated, and
mean different things at different companies. Domains don't.

Someone who reports "I've been in tech for fifteen years" may turn out to have
eleven years of infrastructure, three of data work and two of ML — a completely
different picture from the one in their head, and one they usually haven't
assembled because no single job made them count.

## Present three title families

**1. The longest record** — where the years actually are.
**2. The most recent interest** — where they say they want to go.
**3. The intersection** — usually the real pitch, and usually the least crowded.

For each, name real market titles they'd search for, not descriptions. "Site
Reliability Engineer" and "Platform Engineer" are searchable; "infrastructure
person" is not.

## Then say the uncomfortable part plainly

The market prices the longest record. The most recent interest is where people
*want* to compete and it is usually where they are weakest, because they are
measured against specialists with twice their depth in it.

State the ratio out loud — *"you have eleven years here and two years there"* —
and what it means: in the first pile they're a strong candidate, in the second
they're a career changer competing against people who've done nothing else.

**Then let them choose.** This is not a veto. Someone may have excellent reasons
to take the harder path, and plenty of people succeed at it. What they shouldn't
do is take it *without knowing they took it* — which is what happens by default,
because nobody does this arithmetic unprompted.

If they pick the recent-interest path, say what would make it work: a portfolio
artifact, a specific credential, or the intersection framing as a bridge.

## Write the result as a hypothesis

Populate `source/role_framing.yaml` from the choice, replacing the shipped
examples entirely. Head it:

```yaml
# HYPOTHESIS — derived from the career interview on <date>, not yet tested
# against real outcomes. Revisit after 15–20 logged applications; docs/FRAMING.md
# has the method. Expect to be wrong about at least one of these.
```

Put the chosen family in `title_boost`. Put genuinely mismatched titles in
`title_penalty` — and be careful here: penalise what their record doesn't
support, not what they dislike. Put real credential gaps in `jd_flag`.

**Say out loud that this is a guess.** Its whole purpose is to be corrected by
evidence in Phase 8. A user who thinks it's an answer won't revisit it.

---

# Phase 4 — The resume they already have

Now, and not before, ask whether they have an existing resume.

Deliberately after the interview. Handed over first, it anchors the whole
conversation to what they wrote years ago, and you'll spend the hour confirming
an old document instead of finding what's missing from it.

- **They have one** → read it, diff it against the profile, and ask about every
  discrepancy: dates that don't line up, numbers that disagree, technologies
  listed once with no story behind them.
- **They don't** → say so plainly, and that it doesn't matter. The profile is
  the source document; resumes generate from it per posting. Not having one is
  arguably cleaner — nothing stale to unlearn.

Unresolved items go in the profile's **Open questions** section rather than
quietly disappearing. Each one is a future over-claim.

---

# Phase 5 — Job sources

Three kinds, in descending order of value. Explain the ordering, because it's
counterintuitive and it's what keeps them from drowning in aggregator volume.

**Company watchlist — the best signal.** Direct hits on applicant-tracking
boards. Postings appear before aggregators see them, there's no scraping and no
terms-of-service exposure, and competition is a fraction of anything that
reached a job board. `templates/company_watchlist.yaml` explains how to find a
company's board identifier. It starts empty on purpose.

Help them seed it with 5–10 companies using the three habits in that file:
group by *problem shape* rather than industry label, mine their targets'
customers, and add every company that reaches a real conversation — including
ones that reject them.

Then verify:

```bash
python3 source/job_scout.py --verify
```

**Aggregators — volume.** High volume, low precision. The scoring in
`role_framing.yaml` is what makes them survivable.

**LinkedIn — manual, deliberately.** No usable API, active anti-scraping, and
the terms-of-service risk lands on *their* account. They browse, they paste.

Give them the local-and-hybrid recommendation with the reasoning: remote
postings draw national pools of several hundred to several thousand per req,
while their local market has a fraction of that competition and they have
scarcity value in it. Manual attention should go where the odds are structurally
better. Remote search is for the scanner, where volume is free.

Set `job_filters.yaml` together — freshness, location, comp floor, exclusions.

---

# Phase 6 — One real resume, start to finish

Find an actual posting they'd genuinely apply to and build the whole thing:

```
/build-resume <the JD or a link>
```

**Do this in the first session.** Someone evaluating a tool they downloaded
twenty minutes ago needs to see a finished PDF before they'll invest an hour
more. A markdown file is an unfinished job.

If the posting names a human, say so and offer to draft the outreach. That
message is worth more than the resume — nearly every process that goes anywhere
starts with a person rather than a portal.

---

# Phase 7 — Log it, then show them the dashboard

```bash
python3 source/pipeline.py --serve
```

Warn them now, while the numbers are still empty and it costs nothing to hear:

**Distrust a flattering number.** This dashboard reported roughly double the
true hit rate until three bugs were found — dead processes counted as
conversions, an authoring convention misread as "never submitted," and no
staleness rule at all. A tracker that flatters you makes you do more of what
isn't working.

Tell them the rule that fixes most of it: **an application with no reply after
three weeks is a rejection, not an open question.**

---

# Phase 8 — Transcription dry run

Prove the pipeline works *before* a real interview depends on it.

```bash
mkdir -p ~/Desktop/recordings
```

Have them record ten seconds of anything, drop it in, and run `/transcribe`.
Confirm both files appear — plain prose and `.timed.txt`.

Then make the case for the habit, because it's the highest-leverage one in the
system and it sounds like overkill until it isn't:

Memory reshapes a conversation within hours. It inverts numbers, hardens maybes
into commitments, and quietly rewrites what you were told. Three real cases from
this system's use: a hiring manager said a licensing deal **saved** about a
million a year and it was remembered by the next day as **costing** a million; a
posting described a "buy over build" strategy while the executive argued the
exact opposite in person; a recruiter named the specific question two previous
candidates had failed.

Note the consent point: check local law, many places require one party only, and
on a video call *"mind if I record so I can take proper notes?"* costs nothing.

---

# Phase 9 — Deferred, and say so

Do not attempt this during onboarding. Tell them it's coming and why it has to
wait.

After **15–20 logged applications**, group outcomes by the *title* of the
posting and look for the phrase that keeps appearing in the rejections. That
corrects the Phase 3 hypothesis with real evidence. `docs/FRAMING.md` has the
method.

This is the step people skip and it has the highest payoff of anything here. One
run of it found a single phrase — *"X+ years as a Software Engineer"* — behind a
run of consecutive rejections, while customer-facing titles at comparable
companies advanced to late rounds. That took about twenty applications to see
and was invisible until the outcomes were grouped by title.

**Offer it unprompted** when the application count crosses 15.

---

## Things that go wrong in onboarding

**Writing something they can't defend.** The most important habit in the system.
You will infer a capability from an adjacent fact and write it as experience.
When corrected, flag it immediately — and remember the correction for the rest
of the session.

**Letting a personal project drift into work experience.** Keep that line sharp.
It is the single easiest way to put someone in a room defending a claim they
never made.

**Writing a loss as a credential.** "Reached the final round at X" tells the
reader they lost.

**Rushing Phase 3 because the user seems certain.** Someone who announces their
target in the first five minutes is exactly who needs the arithmetic, because
they've skipped it too.

**Filling the profile with the resume.** If the profile reads like the document
they handed you, the interview failed. The value is in what isn't on the resume.
