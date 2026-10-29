# Deriving your own framing rules

The highest-payoff step in this system, and the one people skip because it
requires data you don't have on day one.

## The claim

Two postings can describe the same seniority, the same compensation and nearly
the same work, and screen you completely differently — because the **title**
decides which pile you land in.

A posting titled *Senior Software Engineer* counts years spent writing
software. One titled *Forward Deployed Engineer* counts years spent standing
between customers and systems. If your record is the second kind, the first
title rejects you regardless of how well the body of the JD fits.

Most people treat this as noise. It is signal, and it is measurable.

## The method

**You need 15–20 logged applications before this works.** Fewer than that and
you are pattern-matching on coincidence.

**1. Mark every application with a binary outcome.** Not "rejected" vs
"waiting" — *did it produce a human conversation, or did it die with no human
contact at all?* The second category is a screen failure, and screen failures
are what framing fixes.

**2. Group by the title of the posting.** Not the company. Not the industry.
Not the comp band. The title, as written.

**3. Read the titles in the no-contact group and look for a repeated phrase.**

That's it. The phrase will be more specific than you expect, and once you see
it you will not be able to unsee it.

## A worked example

One run of this exercise, after about twenty applications, found the no-contact
group dominated by a single phrasing:

> *"X+ years as a Software Engineer"*

A run of consecutive rejections shared it. Meanwhile titles built around
*deployment*, *solutions*, *integration* and *forward deployed* were advancing
to third and fourth rounds at companies of similar size and compensation.

Same person, same resume quality, same seniority. The difference was which
history the screen was counting.

**The non-obvious part:** several of the advancing postings *also* demanded
"7+ years of software engineering experience" in the requirements. So the JD
body was not the signal — the title was. That's why in `role_framing.yaml`, JD
phrases only annotate a result with a warning, while titles carry scoring
weight.

## Writing it down

In `templates/role_framing.yaml`:

- **`title_boost`** — titles that advanced you. Scored up.
- **`title_penalty`** — titles that rejected you. Scored down, **not dropped**, so a strong match on other signals can still surface.
- **`jd_flag`** — phrases in the body worth a warning. These never drop a result; they tell you the gap before you spend an afternoon on it.

## Cautions

**Your phrase will be different from the example.** If your background *is*
software engineering, penalising "software engineer" is exactly backwards.
Delete the examples and derive your own.

**Don't populate this from preference.** It is tempting to boost the titles you
*want* and penalise the ones you find unappealing. That produces a scanner that
agrees with you and a search that doesn't work. Populate it from outcomes only.

**Re-derive it every month or so.** Your record changes as you accumulate
rounds, and a pattern that held at twenty applications may not hold at sixty.

**A penalty is not a prohibition.** The weights are deliberately set so that an
otherwise-excellent match still surfaces with a lower score. You want to see
those and decide, not have them silently filtered.

## What this does not fix

Framing addresses **round-0 losses** — dying at the screen with no human
contact. If your losses cluster in late rounds instead, the problem is
different and this file won't help. Build the round-loss table in
`APPLICATIONS.md` to find out which problem you actually have before you spend
effort on the wrong one.
