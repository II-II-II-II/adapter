# The playbook

The tooling is the easy half. This is the method — in the order you actually do it.

---

## 1. Tell your career story out loud (about an hour)

**Don't fill in the profile template by typing.** Open a session and say:

> *"I'm new here. Walk me through setting this up."*

The assistant runs the `onboard` skill and interviews you — chronologically,
oldest role first, writing `master_profile.md` as it goes. It saves after each
role, so you can stop and resume across several sittings rather than committing
to an uninterrupted hour.

**You do not need a resume, and you do not need to know what job you want.**
Both are expected to be missing. The interview is what produces them.

Why this works better than a form: you will remember things in conversation
that you would never think to type. The deadline you shouldn't have hit. The
thing that broke at 2am and what it turned out to be. The redesign forced by a
supply shock. Those are your best interview material, and they are exactly what
people leave out of a resume because they don't feel like achievements.

**Push back when it writes something you can't defend.** This is the most
important habit in the whole system. An assistant will infer a capability from
an adjacent fact and write it as experience. Every time you correct it, add an
honesty flag so the correction survives. Real corrections from this system's
own development:

- It disclaimed a capability because the profile was silent on it — *silence is not absence; ask.*
- It described user administration as identity-platform engineering — *two very different things.*
- It let a demo project drift into a work-experience section — *keep that line sharp.*
- It wrote a lost final round as a credential — *"you are telling someone I lost badly."*

## 2. Work out what you're actually selling

Once the history exists, the assistant does arithmetic you can't easily do for
yourself: it tallies your years by **domain** rather than by job title, and
shows you three candidate title families — where your longest record is, where
your most recent interest is, and the intersection of the two.

This matters most if you don't know what to apply for, and it matters almost as
much if you think you do. The market prices your longest record; the field
you're most excited about is usually where you're weakest, because you're
measured there against people who've done nothing else. Seeing the ratio — *ten
years here, two years there* — changes what you do next.

The result seeds `role_framing.yaml` as an explicit **hypothesis**, to be
corrected by real outcomes in step 5.

## 3. Then hand over your old resume, if you have one

Deliberately after the interview, not before. Given first, it anchors the whole
conversation to what you wrote years ago and you spend the hour confirming an
old document instead of finding what's missing from it.

If you don't have one, that's genuinely fine — arguably cleaner, since there's
nothing stale to unlearn.

## 4. Answer the follow-up questions

Expect to be asked about dates that don't line up, numbers that are missing,
and technologies mentioned once with no context. Resolve them — each unresolved
item is a future over-claim. Keep the leftovers in the **Open questions**
section rather than letting them disappear.

---

## 5. Wire up the job sources

Three kinds, in descending order of usefulness.

**Company watchlist (best signal).** Hit companies' own applicant-tracking
boards directly. `templates/company_watchlist.yaml` starts empty and explains
how to find a company's board identifier for Greenhouse, Lever, Ashby and
BambooHR. Build it as you go — add every company you'd genuinely say yes to,
including the ones that reject you. Verify what you've added with:

```bash
python3 source/job_scout.py --verify
```

**Aggregators (volume).** The scanner also pulls broader sources. High volume,
low precision — the scoring in `role_framing.yaml` is what makes it survivable.

**LinkedIn — manual, and this is deliberate.** LinkedIn has no usable API for
this, actively blocks scraping, and the terms-of-service risk lands on *your*
account. Getting banned mid-search would be genuinely damaging.

So the workflow is: **you browse, you paste.** When you find something, paste
the URL or the full text into the session and ask for an assessment. In practice
this is where many of the best roles come from, because the postings that never
reach an aggregator are the ones with the least competition.

**One strong recommendation: filter LinkedIn to local and hybrid only.**

Remote postings draw national applicant pools — several hundred to several
thousand per req. Your local market has a fraction of the competition and you
have scarcity value in it. If you're going to spend attention manually, spend
it where the odds are structurally better. Use remote search for the
watchlist-and-scanner path, where volume costs you nothing.

## 6. Correct your framing with real evidence

Step 2 gave you a hypothesis. This replaces it with data.

After 15–20 logged applications, group outcomes by the **title** of the posting
and look for the phrase that keeps appearing in your rejections. Then rewrite
`role_framing.yaml`. Full method in [FRAMING.md](FRAMING.md).

This is the step people skip, and it's the one with the highest payoff. Expect
the hypothesis to be wrong about at least one thing — that's what it's for.

---

## 7. Build documents per application

```
/build-resume <paste the JD or a link>
```

The skill reads the posting verbatim, checks it against your framing rules,
drafts from the profile, and renders a PDF. Non-negotiables baked into it:

- **A markdown file is an unfinished job.** The deliverable is a PDF.
- **Name real gaps plainly.** It reads as confidence, not weakness — *in a
  competitive national pool.* Locally, where you have scarcity value, don't
  volunteer reasons to pass on you.
- **Never claim what the profile flags.** Ask instead.
- **If the posting has a named human, say so and offer to draft the outreach.**
  That message is worth more than the resume.

## 8. Log it when you send it

Add the row to `APPLICATIONS.md` at submission. Then:

```bash
python3 source/pipeline.py --serve
```

**Expect the first dashboard to be wrong, and distrust a flattering number.**
This system reported roughly double the true hit rate until three bugs were
found: dead processes counted as conversions, an authoring convention misread as
"never sent," and no staleness rule at all. The corrected number was bad enough;
the cold-application number underneath it was far worse. A tracker that flatters
you makes you do more of what isn't working.

---

## 9. Record every interview

**This is the highest-leverage habit in the system.** Check your local laws on
consent; many places require only one party, and in a video call asking *"mind
if I record so I can take proper notes?"* costs nothing.

```
/transcribe
```

Transcription runs on-device. Nothing is uploaded — which is what makes it
defensible for a conversation with a real person in it.

**Why it matters more than it sounds:** memory reshapes conversations within
hours. It inverts numbers, hardens maybes into yes, and quietly rewrites what
you were told. Real examples from this system's use:

- A hiring manager said a licensing arrangement **saved** about a million a year. By the next day it had been remembered as **costing** a million — and a mock answer built on the wrong direction would have been embarrassing in the room.
- A job description said the company followed a "buy over build" strategy. In conversation the same executive said the opposite, at length. The transcript caught the contradiction; memory had kept the JD's version.
- A recruiter named the exact question two previous candidates had failed. That one line shaped an entire interview, and it would have been paraphrased into uselessness within a day.

Both a plain and a timestamped transcript get written, so a disputed line can
be checked against the audio rather than argued about.

## 10. Mock the next round from the last one

```
/mock-interview
```

Build questions from the **actual transcript** of the previous round, plus the
JD and what you know about who's in the room — not from a generic question
bank. Answer them cold, in one take, recorded. Then transcribe and grade.

What this catches that nothing else does: length (most answers run two to three
times longer than they should), the tell where you reach for a bigger story to
avoid a weak answer, and factual errors you'd never notice while talking. One
pass through this found a confidently wrong answer about infrastructure state
management — on a requirement the JD listed as mandatory expertise.

## 11. Prep each room separately

An on-site with three interviewers is three different interviews. Find out who
they are and what they own before you go — public profiles are usually enough
to learn whether someone came up through engineering, product or operations,
and that changes what they'll ask.

Two patterns worth knowing:

**Ask the recruiter what the interviewers care about.** An agency recruiter who
has placed people at that company before may tell you the question that keeps
sinking candidates. That is the single most valuable piece of intelligence
available in a job search, and it is usually free for the asking.

**Calibration is per-company and sometimes inverted.** One hiring manager will
want you thinking big and proposing a roadmap. Another will read exactly that
as a flight risk — someone who won't be satisfied in the role on offer. The
same enthusiasm wins one room and loses the other. Research which you're in.

---

## 12. Read your funnel honestly, then change strategy

Rebuild the round-loss table every few weeks and look for where you actually
lose. Two findings worth testing against your own data:

**Warm versus cold is usually the dominant variable.** If most of your real
conversations came from humans rather than portals, more applications is the
wrong answer — more humans is the right one.

**You may be competing on your weakest credential.** It is easy to chase the
field you're most excited about rather than the one you have the longest record
in — and to lose late rounds repeatedly to people with more depth in it, while a
much stronger credential sits unused one title away. Pivoting to the titles that
matched the longer record changed the response rate immediately.

The lesson generalises: **apply where your longest experience is, not where
your most recent interest is.** They are often not the same place, and the
market prices the former.
