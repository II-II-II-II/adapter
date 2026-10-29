# Master Career Profile — TEMPLATE

> **This is the single most important file in the system.** Everything else —
> resumes, cover letters, interview prep — is generated from it. Spend an hour
> here and the rest gets easier. Skip it and you will get generic output.
>
> **How to fill it in:** don't type it. Talk. Open a session and say *"I want to
> build my master profile — interview me about my career."* Then answer
> questions for an hour. The assistant writes this file as you go and asks
> follow-ups where your answers are thin. You will remember things in
> conversation that you would never think to type into a form.
>
> Delete every instruction block (`>`) as you fill each section in.

---

## ⚠️ Honesty flags — the convention that makes this work

The failure mode of AI-written resumes is confident over-claiming: the
assistant infers a capability from an adjacent fact, writes it as experience,
and you don't catch it until someone asks you about it in an interview.

**Fix it with explicit markers.** Use these inline, anywhere in this file:

| Marker | Meaning |
|---|---|
| `[RESUME-SAFE]` | Verified. Claim it directly, no hedging. |
| `[PERSONAL]` | Your own project, not employer work. Never let it drift into a work-experience section. |
| `[DEMO]` | Built to learn, never ran in production. The most dangerous category — label it. |
| `[STALE: <year>]` | You did this, but years ago. Flag before claiming currency. |
| `[FLAG: <question>]` | Unresolved. The assistant must ask you before using it. |
| `[DO NOT CLAIM]` | Explicitly off-limits. Include the reason. |

Two rules worth stating because they are the ones that get violated:

**Silence is not absence.** If this file doesn't mention a technology, that
means nothing about whether you know it. An assistant must **ask**, never
write a disclaimer like "no experience with X" because the profile is quiet.

**Adoption is not deployment.** Driving a tool's adoption inside a company is
not the same as having built and shipped it. Keep that line sharp.

---

## Identity

> Name, location, phone, email, LinkedIn, GitHub. Exactly as you want it to
> appear on a document — this gets copied verbatim into resume frontmatter.

- **Name:**
- **Location:**
- **Contact:**
- **Links:**

## Search constraints

> The hard boundaries. Be honest here; a filter you don't believe in produces
> applications you won't follow through on.

- **Geography:** remote only / hybrid in <metro> / onsite acceptable in <metro>
- **Compensation:** your floor, and whether it's base or total
- **Travel ceiling:**
- **Non-negotiables:** (clearance, drug testing, industries you won't enter, hours)
- **Timeline pressure:** runway, notice period, hard dates

## How you want to be read

> Two or three sentences. Not a summary of your resume — the thing you want a
> stranger to conclude about you after thirty seconds. Write it in your own
> voice; the phrasing often survives into cover letters.

## Target role families

> The 2–4 shapes of job you can credibly take. Name the titles, because titles
> are what you'll be filtering on. For each, note what makes you a real
> candidate rather than an aspirational one.

1.
2.
3.

---

## Career history

> Reverse chronological. For each role, the instruction that matters:
> **write what you did, with numbers, not what you were responsible for.**
> "Owned the platform" is worthless. "Migrated a live production estate from
> bare metal to colocation to AWS over three years without a customer-visible
> outage" is a resume bullet, an interview story, and a credential.
>
> Include the things that felt like survival rather than achievement — the
> deadline you shouldn't have hit, the thing that broke at 2am, the redesign
> forced by a supply shock. Those are your best interview material and they are
> exactly what people leave out.

### <COMPANY> | <City, ST>
*<Title>* | <Mon YYYY> – <Mon YYYY>

**Context:** size, funding, your remit, what was hard about the environment

**What you actually did:**
-
-

**Numbers:** scale, accuracy, volume, revenue, headcount, uptime, cost
**Failures and what you learned:**

---

## Technical inventory

> A flat keyword list, grouped. Purpose is keyword matching against JDs, so
> breadth is fine here — but **flag honestly**, because this is the section an
> assistant will mine hardest and over-claim from.

- **Cloud / infrastructure:**
- **Networking:**
- **Languages:**
- **Data:**
- **AI / ML:**
- **Security & compliance:**
- **Tooling:**

## Projects

> Named projects only, not task descriptions. A project has a name, a purpose,
> and ideally a URL. "Built an evaluation harness" is a task; call it by its
> name or leave it inside a role instead.
>
> Mark each one `[PERSONAL]`, `[DEMO]`, or production. If it's public, link it —
> a repo someone can read is worth more than any claim about it.

**<NAME>** — `[PERSONAL]` / `[DEMO]` / production · <url>
> What it does, the hard part, and how you know it works.

## Education & credentials

> Degrees, certifications, coursework. **Also list what you do NOT have**, if
> it's something postings routinely ask for — absent certifications are a
> recurring screen and you want the assistant to stop claiming them.

## Voice reference

> Paste one piece of writing you did yourself — a real cover letter, a long
> email, a post. The assistant uses it to match your voice instead of producing
> LLM-flavoured prose. This is the single cheapest quality improvement available
> and almost nobody does it.

---

## Open questions

> A running list of things the assistant flagged and you haven't resolved.
> Clear these as you go; each one is a potential over-claim.

-
