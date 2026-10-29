# Applications

> The system's source of truth. `pipeline.py` parses this file to build the
> dashboard, so the structure matters more than the prose.
>
> **The one rule that keeps the numbers honest: log an application when you
> SEND it, not when you build the documents.** Logging at build time produces
> phantom applications and a hit rate that flatters you.

## How status is read

`pipeline.py` reads the **start** of the status cell to classify a row, so lead
with the state marker and put commentary after it:

| Write this first | Classified as |
|---|---|
| `**❌ REJECTED <date>** — …` | closed |
| `**✅ INTERVIEW <date>** …` | live |
| `**Submitted <date>.** …` | awaiting |
| `**Ready to send** …` / `**NOT SENT**` | built, not sent |

Two behaviours worth knowing:

**Silence is an answer.** An application with no reply after 21 days counts as
a rejection in the funnel math, not an open question. Change `STALE` in
`pipeline.py` if you disagree.

**The In-flight table wins.** If a company appears in both tables, its
In-flight state overrides its application row — that's where you record the
real outcome once a conversation starts.

---

| Date | Company | Role | Location / Remote | Comp (posted) | Docs | Status |
|---|---|---|---|---|---|---|
| | | | | | | |

---

## 🔥 In flight — active conversations

> Only rows where a live human conversation is happening. A recruiter screen
> that hasn't produced contact with the employer is **not** in flight; it's an
> application. Keeping this bar high is what makes the number mean something.
>
> Record what was actually said, with names, dates and quotes. This becomes
> your interview prep for the next round, and the quotes are what catch the
> difference between what you remember and what happened.

| Company | Role | Comp | Status |
|---|---|---|---|
| | | | |

---

## Not pursued / closed

> Roles you deliberately skipped, and why. Worth keeping — the reasons form a
> pattern, and the pattern tells you what you actually want.

| Date | Company | Role | Why |
|---|---|---|---|
| | | | |

---

## 📉 Round-loss analysis

> Rebuild this every few weeks. It is the most useful thing in the file.
>
> Group every loss by the round it died in, counting "rejected or ghosted with
> no human contact at all" as **round 0**. Then count how many of your
> conversations came from a cold application versus a human — a recruiter, a
> referral, inbound interest.
>
> The author's own version of this table showed 19 of 26 losses at round 0, and
> a true cold-application-to-conversation rate of roughly 12% against a much
> higher warm-channel rate. That one number changed the whole strategy: the
> screen was the problem, not the interview. Yours will say something different,
> and you cannot know what until you build the table.

| Round lost | Count | Who |
|---|---|---|
| **Round 0** — no human contact | | |
| **Round 1** | | |
| **Round 2** | | |
| **Round 3+** | | |
| **Final stage** | | |
