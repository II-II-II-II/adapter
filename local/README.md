# Adapter on Windows, with everything running on your own computer

No subscription, no account, nothing sent to a company. The AI runs on your
graphics card.

You don't need to know how to code. You will double-click things.

---

## What you're about to build

A tool that interviews you about your career, turns that into a document
everything else is built from, works out what jobs you should actually be
applying for, writes a tailored resume for each one, and transcribes your
interviews so you can go back and check what was really said.

**Set aside about an hour for setup**, most of it waiting for downloads, plus
another hour or so for the interview — which you can break up across days.

## What you need

- Windows 10 or 11
- An NVIDIA graphics card (an RTX 3060 or better). It still works without one;
  transcribing interviews is just slow.
- About 30 GB of free disk space
- **Python 3.12** — see below, this one matters

### Installing Python (do this first)

There's a trap here. The big download button on python.org gives you version
3.13, and the chat window doesn't support it yet. You need **3.12**.

1. Go to **https://www.python.org/downloads/release/python-3128/**
2. Scroll to the bottom, click **Windows installer (64-bit)**
3. Run it. On the first screen, **tick "Add python.exe to PATH"** before
   clicking Install. This is the step everyone misses.

---

## Step 1 — Install

Double-click **`Setup Adapter.bat`**.

A black window opens and starts installing. It takes 15–30 minutes. Most of
that is downloading the AI model, which is about 9 GB.

You can leave it alone. It'll tell you when it's done.

> **If Windows shows a blue "Windows protected your PC" box:** click **More
> info**, then **Run anyway**. That appears for any file downloaded from the
> internet that Microsoft hasn't seen before.

## Step 2 — Open your chat window

Double-click **`Start Adapter.bat`**.

A black window opens — **leave it open**, it's running the chat. Your browser
opens by itself after about 20 seconds.

The first time, it asks you to create an account. **This is only on your own
computer.** The email and password are stored on your hard drive and go
nowhere. Use anything you'll remember.

You'll land in a chat window that works like ChatGPT.

## Step 3 — Teach it what to do

This is the only fiddly part, and you only do it once.

1. Click your **name** at the bottom-left, then **Settings**
2. Click **Personalization**, then **System Prompt**
3. Open the file **`local\SYSTEM_PROMPT.md`** in Notepad
4. Select all of it (**Ctrl+A**), copy (**Ctrl+C**)
5. Paste into the System Prompt box (**Ctrl+V**), click **Save**

At the top of the chat window, make sure the model selector says something
starting with **qwen** — that's the AI running on your graphics card.

## Step 4 — Do the interview

Type **hello** and press enter.

It'll start asking about your career, beginning with your first relevant job.
Answer like you're talking to someone. Full sentences aren't necessary.

**Three things that make this work:**

**Give it numbers.** How many people, how many customers, how many sites, how
big the budget, how long it ran. Numbers are the most valuable thing you can
give it. "A lot" is worth nothing on a resume; "around 300 employees" is worth
a great deal.

**Tell it the bad nights.** The outage, the thing that broke, the deadline you
shouldn't have hit, the system everyone hated that you kept alive anyway. These
feel like complaints rather than achievements, which is exactly why nobody puts
them on a resume — and exactly why they're the best thing you'll say in an
interview.

**Correct it when it's wrong.** It will occasionally write something you didn't
say. Tell it. It'll fix it and won't repeat it.

You can stop whenever you like and come back — just reopen the same chat.

## Step 5 — Build your profile

When you're done talking:

1. Click the **chat's name** at the top of the window
2. Choose **Download**, then **Plain text**
3. Double-click **`Build My Profile.bat`**

You don't have to put the download anywhere special. `Build My Profile.bat`
looks through Downloads, your Desktop and the Adapter folder, shows you what
it found, and lets you pick if there's more than one.

It writes `source\master_profile.md` and then prints a list of things to check.

### Read what it wrote. Properly.

**The AI running on your computer is much smaller than ChatGPT or Claude, and
it makes mistakes.** It is good at the conversation and less good at writing
the document. Two real examples from testing, both with the same model you
just installed:

- The person said *"we **lost** 14,000 gallons of product."* It wrote
  *"**saving** 14,000 gallons of product."* Same number, opposite meaning — and
  that is the kind of line a hiring manager asks you to explain.
- The person said *"I have not written Python. Do not put that down."* It left
  that out of the document entirely, so the warning simply disappeared.

Both of those now get caught and printed. That's what the checklist is for:

- Every **job title** it wrote — check you actually said each one
- Every **number**, shown next to the sentence you actually said it in, so a
  reversal like the one above is obvious at a glance
- Everything you said you had **not** done, and how many of those it recorded
- Every **number you mentioned that didn't make it in**
- Anything it marked `[FLAG: ...]` because it knew it didn't know

Open `source\master_profile.md` in Notepad and fix anything wrong. **Ten
minutes here saves you from an interview where you get asked about something
that isn't true.**

This is the single most important step in the whole process. Everything else is
built from this file.

## Step 6 — Work out what to apply for

Back in the chat, say:

> **I've finished my profile. What kinds of jobs should I be applying for?**

It'll add up your years by *type of work* rather than by job title, and show
you three directions: where your experience actually is, where you say you want
to go, and the overlap.

**This is the most useful thing in here, especially if you don't know what to
search for.** Most people have never added up their own years this way, because
no single job ever made them do it. The answer is often not what they expected.

## Step 7 — Record your interviews

Put any recording in the **recordings** folder on your Desktop, then open the
black window and type:

```
.venv\Scripts\python.exe source\transcribe.py "%USERPROFILE%\Desktop\recordings\yourfile.m4a" transcripts\interview1.txt
```

You get two files: the plain text, and one with timestamps so you can jump back
to any line in the audio.

**The recording never leaves your computer.** That's the point — there's
another person's voice on it.

Check your local laws on recording. Most US states need only one party to
consent. On a video call, *"mind if I record this so I can take proper notes?"*
costs nothing and is almost never refused.

---

## When something goes wrong

### First: double-click `Share My Log.bat`

It makes one plain-text file on your Desktop and opens it. Send that file to
whoever gave you this.

It has your Windows version, your graphics card, your Python versions, which
packages installed and which didn't, and every error message the scripts hit —
with timestamps and exit codes. That's usually enough to tell what happened
without anyone having to sit at your computer.

**It does not contain anything you said in the interview**, and nothing out of
your profile, resumes, applications or transcripts. The scripts never write
your career history to a log. It's plain text — open it and check, that's why
it's plain text.

It works even if setup failed in the first ten seconds; it re-checks the
machine rather than relying on a log that never got written.

**Along with the file, say in your own words:** what you clicked, what you
expected, and what happened instead. That one sentence is usually the fastest
clue in the whole bundle.

### The common ones

**"Python was not found"** — Python isn't on your PATH. Reinstall it and tick
"Add python.exe to PATH" on the first screen.

**Setup stops with a red error about open-webui** — you're on Python 3.13.
Install 3.12 from the link at the top and run setup again.

**Browser says "can't reach this page"** — the chat takes 20–30 seconds to
start. Wait, then refresh. If the black window closed, run `Start Adapter.bat`
again.

**The AI is very slow, or your fans are loud** — normal. Your graphics card is
doing real work. If it's unusably slow, the model may be too big for your card:
open the black window and run `ollama pull qwen3:8b`, then pick that model at
the top of the chat.

**It said something about my career that I never told it** — that's the known
weakness. Correct it in the chat, and fix the file by hand after Step 5.

**"Couldn't install Ollama automatically"** — install it yourself from
[ollama.com/download](https://ollama.com/download), then run
`Setup Adapter.bat` again. Everything else is already done, so the second run
is quick.

**`Build My Profile.bat` says it can't find a saved chat** — it looks for a
`.txt`, `.json` or `.md` file over 2 KB, saved in the last 30 days, in
Downloads, Desktop or the Adapter folder. If you saved it elsewhere, move it to
your Desktop and try again.

**Ollama rejected the request / something about memory** — the model is too big
for your card. Open a Command Prompt and run `ollama pull qwen3:8b`, then
select that model at the top of the chat window.

---

## What this can't do

**It won't write as well as ChatGPT or Claude.** You're trading quality for
privacy and for not paying anyone. That's a real trade, and for the interview
step it's a fine one — the value is in the questions it asks you, not its prose.

**It can't browse job sites for you.** You find postings, you paste them in.

**It won't replace knowing someone.** Nearly every job that actually happens
starts with a person rather than a web form. This makes you faster and better
prepared. It doesn't make you connected.
