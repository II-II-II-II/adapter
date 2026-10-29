# Adapter

**A job-search system you run with an AI assistant in your terminal.** Local
transcription of your interviews, resumes tailored per posting, a funnel that
doesn't flatter you, and a method for working out why you're actually losing.

Built during a real job search after a layoff. Every opinionated thing in here
is opinionated because something went wrong first.

> **There is no app and no sign-up.** It's markdown, YAML and a few Python
> scripts. An AI coding assistant reads the files and runs the commands — the
> assistant is the interface.

---

# Start here

Two ways in. Pick the one that matches what you have.

## A. Windows + an NVIDIA card, no subscription, nothing leaves your machine

Everything runs on your own GPU. No account, no API key, no monthly fee. You
get a chat window in your browser that interviews you about your career and
writes the document the rest of the system builds from.

**You need:** Windows 10 or 11, an NVIDIA card (8GB or better), about 25GB
free, and an hour where you can talk about your work history.

**Install Python 3.12 first — not 3.13.** The chat window doesn't support 3.13
yet, and 3.13 is what python.org's big green button gives you. Get it here:
[python.org/downloads/release/python-3128](https://www.python.org/downloads/release/python-3128/)
— scroll to the bottom, take **Windows installer (64-bit)**, and on the very
first screen **tick "Add python.exe to PATH"**.

Then download this repository (green **Code** button → **Download ZIP**),
unzip it anywhere, and double-click these in order:

| | Double-click | What happens |
|---|---|---|
| 1 | **Setup Adapter.bat** | Installs everything. 20–40 minutes, mostly downloading. Lots of text scrolls past — that's normal. |
| 2 | **Start Adapter.bat** | Opens your chat window in a browser. Leave the black window open. |
| 3 | *(in the browser)* | Make a local account — it exists only on this PC. Then paste in the system prompt, as [local/README.md](local/README.md) shows. |
| 4 | *(in the browser)* | Say hello and talk about your career. Stop and come back whenever you like. |
| 5 | *(in the browser)* | Download the chat: click its name at the top → **Download** → **Plain text**. |
| 6 | **Build My Profile.bat** | Turns the conversation into `source/master_profile.md`, then prints a list of things to check. |
| 7 | — | **Read that list and fix the file.** This step is not optional; see below. |

**If anything at all goes wrong — double-click `Share My Log.bat`.**

It writes one plain-text file to your Desktop with your Windows version,
graphics card, Python versions, which packages installed, and every error the
scripts hit. Send that file. It contains **nothing** from your interview and
nothing from your profile — the scripts never write your career history to a
log. Open it and read it first if you want to; it's plain text on purpose.

You can run `Share My Log.bat` even if setup failed immediately — it checks the
machine fresh rather than relying on a log that was never written.

> ### Read this part before you trust the output
>
> A model small enough to run on a 12GB card is noticeably weaker than a
> frontier one. In testing it kept every real story and invented nothing of
> substance — but it **turned "we lost 14,000 gallons" into "saved 14,000
> gallons"**, and it dropped a "don't claim I know Python" correction
> entirely. Both now get caught and printed for you to check.
>
> So `Build My Profile.bat` ends with a checklist: every job title it wrote,
> every number set beside the sentence you actually said it in, and everything
> you told it you had *not* done. **Work through it.** The whole point of this
> system is not claiming things you can't defend in a room.

## B. Mac, Linux, or Windows with Claude Code

```bash
git clone <your-fork> adapter && cd adapter
./setup.sh
claude
```

Then say: ***"I'm new here. Walk me through setting this up."***

`setup.sh` detects your hardware — Apple Silicon, NVIDIA, or CPU — and
installs the matching transcription backend. The assistant takes it from
there: it runs the career interview, works out which job titles your record
actually supports, and builds your first tailored resume before you've typed a
command.

Not using Claude Code? Paste [BOOTSTRAP.md](BOOTSTRAP.md) into whatever
assistant you do use. Full instructions in [SETUP.md](SETUP.md).

**No resume and no idea what to apply for is the expected starting point**, not
a problem to solve first. The interview is the source document; everything
generates from it.

---

## Why this exists

The job market is getting harder, and the parts of it that are getting harder
fastest are the parts where a person used to read your application.

Most job-search tooling optimises for volume — more applications, faster. That
is the wrong variable. This optimises for **knowing what's actually happening**:
which framing gets you screened out, which channels produce real conversations,
what was genuinely said in the room versus what you remember.

## The four things that make it different

**1. Record and transcribe your interviews, locally.**

Memory reshapes a conversation within hours. It inverts numbers, hardens
maybes into commitments, and quietly rewrites what you were told. Real cases
from this system's own use:

- A hiring manager said a licensing arrangement **saved** about a million a year. By the next day it had been remembered as **costing** a million.
- A posting described the company's strategy as "buy over build." The executive, in person, argued the exact opposite at length.
- A recruiter named the specific question that two previous candidates had failed.

All three would have been lost or inverted inside a day. Transcription runs
on-device — nothing is uploaded, which is what makes it defensible for a
recording with another person's voice in it.

**2. Derive your framing from your own rejections.**

Two postings can describe the same job and screen you completely differently,
because the **title** decides which pile you land in. This system's author
found a single phrase — *"X+ years as a Software Engineer"* — behind a run of
consecutive rejections, while customer-facing titles at comparable companies
advanced to late rounds.

You can measure your own version of that. [FRAMING.md](docs/FRAMING.md) is the
method; `role_framing.yaml` is where it gets scored.

**3. A funnel that tells you the truth.**

This dashboard reported a hit rate roughly double the truth until three bugs
were found: dead processes counted as conversions, an authoring convention
misread as "never submitted," and no staleness rule at all. Underneath the
corrected number was a second one that mattered more — applications sent cold
converted at a small fraction of the rate of anything that arrived through a
person.

Seeing that changed the whole strategy. A tracker that flatters you makes you
do more of what isn't working.

**4. Honesty flags in your profile.**

The failure mode of AI-written resumes is confident over-claiming — the
assistant infers a capability from an adjacent fact and writes it as
experience. `master_profile.md` uses explicit markers (`[RESUME-SAFE]`,
`[PERSONAL]`, `[DEMO]`, `[STALE]`, `[DO NOT CLAIM]`) so corrections survive,
and so the assistant asks instead of guessing.

Two rules it enforces: **silence is not absence** — a technology the profile
doesn't mention means nothing about whether you know it, so ask. And
**adoption is not deployment** — driving a tool's adoption is not the same as
having shipped it.

---

## What's in here

```
setup.sh                Hardware detection, install, first-run layout. (Mac/Linux)
CLAUDE.md               Standing rules the assistant reads every session.
BOOTSTRAP.md            Paste-in equivalent for assistants that aren't Claude Code.

Setup Adapter.bat       Windows, no terminal. Installs everything.
Start Adapter.bat       Windows. Opens the local chat window.
Build My Profile.bat    Windows. Interview in, profile document out.
Share My Log.bat        Windows. One diagnostic file, no personal content.

local/README.md         Click-by-click guide for the fully-local Windows path.
local/SYSTEM_PROMPT.md  The interviewer prompt you paste into the chat window.
local/extract_profile.py  Builds the profile, then prints what to verify.
local/_log.ps1          Shared logging. Every step, every exit code.

docs/PLAYBOOK.md        The method, in the order you do it. Start here.
docs/FRAMING.md         How to derive your own title rules from your outcomes.
docs/JD_RECOVERY.md     Pulling postings out of Workday, ADP, Greenhouse, Lever, Ashby.

templates/              Copy these into source/ and make them yours.
  master_profile.md     The hour-long career interview. Everything generates from it.
  APPLICATIONS.md       The tracker the dashboard parses.
  role_framing.yaml     Title scoring rules.
  job_filters.yaml      Freshness, location, comp floor, exclusions.
  company_watchlist.yaml Companies to watch directly. Starts empty; you build it.
  jd_registry.yaml      Joins applications to postings and documents.

skills/                 Assistant workflows.
  onboard/              Career interview, title triangulation, first resume.
  build-resume/         JD in, tailored ATS-safe PDF out.
  mock-interview/       Questions from real transcripts; records and grades you.
  transcribe/           Recording in, transcript in the conversation.

source/                 The scripts.
  job_scout.py          Multi-source scan, scored against your framing.
  pipeline.py           Parses APPLICATIONS.md into a dashboard.
  md_to_pdf.py          Styled, ATS-safe PDF rendering.
  transcribe.py         Local GPU transcription, plain + timestamped.
  mcp_server.py         Optional read-only Gmail/Calendar tools.
```

---

## Three findings worth stealing even if you never run this

**Warm beats cold by a lot.** Only a small fraction of cold applications
produced a human conversation at all, while nearly every late-stage process
came from a recruiter, a referral or inbound interest. If that holds for you,
more applications is the wrong answer and more humans is the right one.

**Apply where your longest experience is, not where your most recent interest
is.** These are often different places, and the market prices the former. It is
possible to spend months losing late rounds in a field you've worked in for a
couple of years, while a decade of deeper experience sits unused one title away.
Pivoting to the titles that matched the longer record changed the response rate
immediately.

**Silence is an answer.** An application with no reply after three weeks is a
rejection, not an open question. Counting it as open is how a pipeline looks
healthy while nothing is happening.

## Limits, honestly

- **Transcription has no speaker labels.** A two-person call comes back as one stream. Usually inferable from content; sometimes genuinely ambiguous.
- **Proper nouns get mangled.** Company and product names especially — check them.
- **LinkedIn is manual on purpose.** No usable API, active anti-scraping, and the terms-of-service risk lands on your account. You browse and paste. [PLAYBOOK.md](docs/PLAYBOOK.md) explains why that's not as bad as it sounds.
- **Transcription without a GPU is slow.** Apple Silicon and NVIDIA are fast; CPU works but a one-hour interview takes 20–40 minutes.
- **Nothing here beats a referral.** This makes you faster and better informed. It does not replace knowing someone.
- **The fully-local model is the weakest link in that path.** At 14B it interviews well and fabricates little, but in testing it reversed the direction of an outcome (a loss written as a saving) and omitted a correction the user had explicitly asked it to record. `Build My Profile.bat` prints both classes of error for you to check, and you have to actually check them. With Claude Code or another frontier assistant, this isn't a concern.
- **Windows is the least-tested path.** The Mac/Linux route has been used daily for months. The Windows scripts are newer; they log everything to `logs/` precisely because they're the ones most likely to surprise you.

## Contributing

The scripts are deliberately small and hackable. If you adapt the framing method
to a different field and it works, a note about what your phrase turned out to
be would be genuinely interesting.

## Licence

MIT — see [LICENSE](LICENSE).
