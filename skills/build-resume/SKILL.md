---
name: build-resume
description: Build a resume tailored to one specific job posting, plus a cover letter when there's a field for one, then render it to a styled ATS-safe PDF. Use whenever the user names a job they want to apply to, pastes a job description or a posting link, asks for a one-pager, or says they found something worth applying for. Covers the whole pipeline — JD in, PDF out — so the work is never left as half-finished markdown.
---

# Build a tailored resume

**The deliverable is a PDF.** A markdown file alone is an unfinished job.
Running the renderer is part of the task, not a follow-up.

---

## 1. Read the posting verbatim

Not a summary. Fetch it live, or use the saved copy in `source/jobs/`. If it's
a JS-only career site, `docs/JD_RECOVERY.md` has the endpoints.

Note explicitly, before writing anything:

- Which requirements the user genuinely clears
- Which they don't — and whether the gap is stated as *required* or *preferred*
- **The exact years-of-experience wording.** "5+ years in X, Y, or a related role" is a door. "8+ years as a Z" is a gate. They are not the same.
- Whether there's a cover-letter field. If not, the pitch goes in the resume's opening blockquote.
- **Comp: base or OTE?** OTE means base is typically 70–75% of the headline.
- Travel, onsite days, clearance, citizenship

**Save a local copy.** Postings get taken down and you'll want the exact
wording when the interview happens three weeks later.

## 2. Check the framing before you write

Read `source/role_framing.yaml`. It holds the user's own empirically derived
title patterns — which framings have advanced them and which have rejected
them — plus JD phrases that warrant a warning.

**If the posting trips a `title_penalty` or a `jd_flag`, say so before
building.** Don't silently drop the role and don't silently proceed. The user
decides whether a known-bad framing is worth the effort.

## 3. Source material

- `source/master_profile.md` — the canonical history. **Honour its honesty flags.**
- `output/resumes/` — prior tailored versions worth cannibalising
- `APPLICATIONS.md` — what has actually landed in rooms

### The honesty rules, which exist because each was violated once

**Never claim what the profile flags.** `[PERSONAL]`, `[DEMO]` and `[STALE]`
mean what they say. A demo project must not appear as work experience.

**Silence is not absence.** If the profile doesn't mention a technology, that
tells you nothing about whether the user knows it. **Ask.** Never write a
disclaimer like "no experience with X" because the file is quiet — that has
produced resumes that undersold real, current skills.

**Adoption is not deployment.** Driving a tool's adoption inside a company is
not the same as having built and shipped it. Keep that line sharp.

**Never write a loss as a credential.** "Reached the final round at X" tells
the reader you lost. Cut it.

**Don't put a correction in a selling document.** If the user corrected an
earlier error, fix it silently. A cover letter that admits a mistake is
spending credibility for nothing.

**No jargon the user can't unpack on demand.** If they can't explain a metric
or acronym cold, it shouldn't be on the page — it's an invitation to a question
they'll fail.

**Check the client-name policy.** Many people cannot name employer clients in
writing. Use "Fortune 500 clients" or a sector descriptor unless the profile
explicitly clears it.

## 4. Write it

Format — `md_to_pdf.py` expects exactly this:

```
---
name: <name>
title: <role-shaped title | 2–3 supporting capabilities>
contact: <city> | <phone> | <email> | <linkedin> | <github>
---
> Optional blockquote — the pitch, when there's no cover-letter field.

## Summary
## What Maps to This Role      ← bolded lead-ins with evidence, not a skills list
## Professional Experience
### COMPANY | City, ST
*Title* | Mon YYYY – Mon YYYY
- bullet
## Projects
## Education
```

**Mirror the posting's own language** in "What Maps to This Role." If they say
"environments and release management," use those words — a human and a keyword
filter are both reading.

**Lead with the requirement they're strongest against**, not with chronology.

**Projects are named projects**, not task descriptions. Capabilities belong
inside a project entry or in "What Maps," never as a standalone project name.

### Gap disclosure is contextual — this one matters

**In a competitive national pool**, naming a real gap plainly builds
credibility and has repeatedly advanced candidates. You're one of hundreds;
honesty differentiates.

**In a local market where the user has scarcity value**, don't volunteer gaps.
There are few qualified local candidates and the hiring manager needs the role
filled. Handing them a reason to pass is a self-inflicted wound. Answer
honestly if asked; don't raise it first.

Check the profile's search constraints to know which situation you're in.

## 5. Cover letter, if there's a field

Same frontmatter. Read the **voice reference** in the profile and match it —
that section exists so the letter doesn't read as generated.

What works: open with a specific, true observation about *this* posting — the
one line that shows you read it rather than skimmed it. Refuse to restate the
resume. One concrete paragraph on why this company and why them. Acknowledge
the volume they're dealing with and ask for something small. Short.

## 6. Render — do not skip

```bash
python3 source/md_to_pdf.py output/resumes/<Company>_<Role>.md
```

Writes the `.pdf` and a `.render.html` alongside. **Confirm the PDF exists and
report its path.** Same command for the cover letter.

## 7. Log it

Add a row to `APPLICATIONS.md` — **when it's sent, not when it's built.**
Logging at build time produces phantom applications and a hit rate that lies.

Record the gaps you named, anything to ask on a first call, and whether the
submission was cold or through a human.

Add the posting to `jd_registry.yaml` so the dashboard can link it.

## 8. Say the thing that actually converts

Cold portal submissions convert at a low single-digit-to-low-double-digit rate.
Nearly every process that goes the distance starts with a person.

**If the posting has a named recruiter, hiring manager, or reachable poster,
say so and offer to draft the outreach.** That message is worth more than the
resume.

And if the user is already represented by an agency at that company, **do not
also submit through the portal** — duplicate submissions create a
candidate-ownership dispute that gets resolved by dropping the candidate.
