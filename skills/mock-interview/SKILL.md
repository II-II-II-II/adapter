---
name: mock-interview
description: Run a mock interview before a scheduled round, or grade a recording afterward. Use when the user names an upcoming interview and wants questions to answer cold, sends an .m4a of a practice run or a real conversation, or asks how a conversation went. Builds questions from the actual job description, prior round transcripts and who's in the room; transcribes locally; returns a prioritised fix list rather than praise.
---

# Mock interview, and post-interview grading

Two modes. Both depend on the same thing: **building from what was actually
said, not from a generic question bank.**

---

# Mode A — before the interview

## 1. Gather the real inputs

A generic mock is close to worthless. Four sources, in order of value:

**Transcripts of prior rounds** (`transcripts/`) — the single best source. Earlier
interviewers tell you the company's actual pain, in their own words, and that's
what the next round will probe. Mine these for constraints, frustrations, and
anything stated as a hard requirement.

**The job description, verbatim** — especially requirements worded as *required*
with the word "expertise." Those are where a weak answer costs the most.

**Who's in the room.** Look them up. A VP of Product, a CTO who came up through
operations, and a hiring manager who already likes the candidate are three
completely different interviews. Someone's background predicts what they ask:
an ex-analytics leader asks about data quality; a long-tenure IT leader asks
about judgment and whether you'll stay.

**Anything the recruiter said.** An agency recruiter who has placed people at
that company may know the specific question that keeps sinking candidates. That
is the most valuable intelligence available in a search and it's usually free.

## 2. Write the questions

Ten to twelve, in a markdown file. Rules:

- **Quote the company's own words back.** If an interviewer said a system "is our big anchor," the question should use that phrase. The user should recognise the room.
- **Include the trap door.** Almost every process has one question that decides it — retention, a known gap, a prior failure. Put it in.
- **Ask at least one about a requirement they're weak on.** The point is to find the bad answer now.
- **End with "what questions do you have for us" and compensation.** Both get fumbled when unrehearsed.

Head the file with the instruction that makes this work:

> Read each aloud, answer on the fly, one continuous recording. No prep between
> questions, no restarts.

## 3. Have them record it

One take. The lack of restarts is the entire value — it surfaces length
problems and verbal tics that a written answer hides.

## 4. Transcribe and grade

```bash
python3 source/transcribe.py <recording> transcripts/<name>_mock.txt
```

Then grade **per question**, with a letter and a one-line verdict, and sort the
output by what to fix first. What to look for:

**Factual errors on required qualifications.** The highest-value thing you will
find. One real example: a candidate said infrastructure state "lives in the Git
repo" — wrong, and wrong on a requirement the JD called mandatory expertise.
They knew better in practice; it came out wrong under pressure. That single fix
was worth more than the rest of the review combined.

**Misread constraints.** Check answers against the transcript of what was
actually said. A cost that was actually a *saving*, a "preferred" heard as
"required" — these invert easily and land badly.

**Length.** Most answers run two to three times longer than they should. Flag
specific ones; don't give general advice about being concise.

**Questions where they have a strong answer and gave a weak one.** Deferring
("I'd need to learn more about your environment") on something they have a real
opinion about is a wasted question. Point at the answer they already own.

**Self-descriptions that work against them.** "Generalist," "Swiss Army knife,"
"I've been all over the place" — breadth claims get read as shallowness. The
specific intersection always beats the range claim.

**Volunteered losses.** "I got to the final round at X" tells the room you lost.

**Then say what was good and leave it alone.** A review that rewrites every
answer produces someone who sounds rehearsed. Name the two or three answers
that worked and tell them not to touch those.

## 5. Write corrected answers for the worst two or three

Full, speakable prose — not notes about what to say. Prioritise ruthlessly:
three rewritten answers the user will actually internalise beat twelve they'll
skim.

## 6. Build a one-page game-day sheet

Phone-readable. Who they're meeting and when, three questions per person, the
trap door with its answer written out, a short do-not list, and five things to
remember. They'll read it in the parking lot.

---

# Mode B — after the interview

## 1. Transcribe it

Same command. Both a plain and a timestamped transcript get written.

## 2. Establish what was actually said before interpreting

**Do this before any analysis.** Memory reshapes conversations within hours —
it inverts numbers, hardens maybes into commitments, and rewrites constraints.

When the user's recollection conflicts with the transcript, **check the
transcript and say so plainly.** And when the disagreement is about a
paraphrase the user wrote themselves, go to the source recording rather than
arguing from their summary. One real case: a mock question the candidate wrote
said a constraint "isn't moving," while the original transcript showed the
interviewer had explicitly left a door open. The paraphrase was more
restrictive than reality, and grading against it produced a wrong critique.

## 3. Report it

- **Outcome first.** Did they advance? Quote the next-step language exactly.
- **New intelligence.** Names, numbers, scope, org structure, anything that contradicts the job description. This is usually the most valuable output — a JD and the person who wrote it often disagree.
- **What worked.** Specifically, so it gets repeated.
- **What to fix**, ranked, with the unforced errors named directly.
- **A grade.** Commit to one. "It went fine" helps nobody.

## 4. Update the record

Put the new intelligence in `APPLICATIONS.md` under the In-flight row — comp,
names, next steps, and anything that corrects an earlier assumption. The next
round's prep is built from this.

---

## One calibration note worth carrying

**Interview calibration is per-company and sometimes inverted.** One hiring
manager wants a candidate thinking big and proposing a roadmap. Another reads
exactly that as a flight risk — someone who won't be satisfied in the role on
offer. The same enthusiasm wins one room and loses the next.

So don't apply a single playbook across a pipeline. Find out which room you're
in, ideally from the recruiter, and prep for that one.
