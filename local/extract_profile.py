"""Turn a saved interview into a master profile, using a local model.

    python extract_profile.py interview.txt [--log] [--model NAME]

Writes source/master_profile.md and prints every line you need to check.

--log appends a technical record to logs/profile-build.log: model name,
timings, word counts, HTTP errors, tracebacks, and COUNTS of the things the
review list found. It never writes what the interview said, or any line of
the profile. That log is designed to be emailed to a stranger; the document
it produces is not.

WHY THIS IS A SEPARATE STEP. A small local model is good at having a
conversation and bad at maintaining a long document across twenty turns of
one. Asking it to do both at once makes it invent things to fill the gaps.
Interviewing and writing are split here for that reason.

IT STILL MAKES MISTAKES. In testing, a 14B model kept every real story and
invented nothing of substance -- but it guessed a job title that was never
given, guessed a city, and dropped one number. Read what it writes. The
review list printed at the end is not optional.
"""
import json
import re
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source" / "master_profile.md"
HOST = "http://localhost:11434"

PROMPT = """You convert a career interview into a master profile document.

ABSOLUTE RULE: every line you write must come from a sentence the person
actually typed in the interview below. Never add a detail because it is
plausible, or because it usually appears in that kind of job. If you cannot
point to the sentence it came from, leave it out.

This document gets sent to real employers. An invented line becomes a question
in a real interview that this person cannot answer.

NEVER GUESS THESE, even though it will feel natural to:
  - a job title they did not state      -> write [FLAG: title not given]
  - a city they did not state           -> write [FLAG: location not given]
  - dates they did not state            -> write [FLAG: dates not given]
  - any number they did not say out loud

KEEP EVERY NUMBER they did give. Headcount, servers, sites, budget, uptime,
duration. Numbers are the most valuable thing in the document.

KEEP THE STORIES. The outage, the bad night, the thing they fixed under
pressure. Those are what get discussed in interviews. Do not compress them
into one generic line.

NEVER REVERSE THE DIRECTION OF AN OUTCOME. If something was lost, spilled,
broken, wasted or went down, it is a loss. Do not turn it into a saving, a
gain or an improvement because that reads better.

    They said:  "We lost 14000 gallons of product."
    WRONG:      "Saved 14000 gallons of product"
    RIGHT:      "Rebuilt the interlock logic after a leak destroyed 14,000
                 gallons of product, so the fault would fail safe"

A reversed number is worse than a missing one. They will be asked about it.

ANYTHING THEY DENIED MUST BE WRITTEN DOWN. If they said they have not done
something, do not know something, or told you not to write something, that is
the most important line in the whole interview. Put it under Open questions as
[DO NOT CLAIM: ...]. Never leave it out just because it is negative.

    They said:  "I have not written Python. Do not put that down."
    You write:  [DO NOT CLAIM: Python - stated they have not written it]

Personal projects go under Projects and are marked [PERSONAL]. Never list a
personal project as employer work. If something was built for an employer,
it belongs under that employer.

If the person corrected themselves or said they had NOT done something, record
it as [DO NOT CLAIM: ...] so it never gets written into a resume.

Output ONLY the document. No preamble, no commentary after it.

# Master Profile — <name>

## Contact

## Experience

### <COMPANY> — <City>
*<Title>* | <Start> – <End>
- <bullet, with the numbers they gave>

## Projects

### <Project name>  [PERSONAL]
- <what it does, and whether it was ever used by anyone else>

## Open questions
- <anything unresolved, one per line>

Here is the interview:

"""


LOG = None  # set by --log


def log(text):
    """Technical events only. See the note in the module docstring."""
    if LOG is None:
        return
    try:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{time.strftime('%H:%M:%S')}] {text}\n")
    except OSError:
        pass  # a broken log must never take the profile down with it


def load_interview(path):
    """Read a chat export. Open WebUI offers plain text and JSON; people pick
    whichever is highlighted, so accept both rather than failing on a choice
    that looked arbitrary to them."""
    raw = path.read_text(errors="replace")

    if not raw.lstrip().startswith(("{", "[")):
        log(f"format: plain text ({len(raw)} chars)")
        return raw

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log(f"format: looked like JSON but failed to parse ({e}); using as text")
        return raw

    # Walk it for anything shaped like a chat message. Open WebUI has changed
    # this structure between versions and will again, so recurse rather than
    # hard-coding a path into it.
    parts = []

    def walk(node):
        if isinstance(node, dict):
            content = node.get("content")
            if isinstance(content, str) and content.strip():
                who = node.get("role", "?")
                parts.append(f"{who}: {content.strip()}")
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    if not parts:
        log("format: JSON with no recognisable messages; using raw text")
        return raw
    log(f"format: JSON, recovered {len(parts)} messages")
    return "\n\n".join(parts)


DENIAL = re.compile(
    r"[^.!?\n]*\b(?:"
    r"i have not|i haven'?t|i've not|i never|i don'?t (?:know|have|do)|"
    r"i can'?t|i'?m not|never (?:used|deployed|shipped|written|done|worked)|"
    r"not (?:production|real|deployed|shipped)|don'?t put|do not put|"
    r"don'?t say|do not say|don'?t claim|do not claim|that'?s just mine|"
    r"only a demo|just a demo"
    r")\b[^.!?\n]*[.!?]?",
    re.I,
)


def sentence_with(number, text):
    """The interview sentence a number came from, for eyeballing direction."""
    for s in re.split(r"(?<=[.!?])\s+|\n", text):
        if re.search(rf"\b{re.escape(number)}\b", s):
            s = " ".join(s.split())
            return s if len(s) <= 150 else s[:147] + "..."
    return None


def check_denials(doc, text):
    """Everything they said they had NOT done.

    A small model omits these far more often than it invents things, and an
    omitted denial is the most expensive error in the document: it leaves the
    user with no record that they already ruled a claim out.
    """
    found = [" ".join(m.group(0).split()) for m in DENIAL.finditer(text)]
    found = [f for f in dict.fromkeys(found) if len(f) > 12][:8]
    if not found:
        return
    recorded = len(re.findall(r"\[DO NOT CLAIM", doc))
    print(f"\nYou said you had NOT done these. The profile records {recorded}.")
    print("Anything missing here, add yourself as [DO NOT CLAIM: ...]:")
    for f in found:
        print("    -", f)


def check_directions(doc, text):
    """Show each kept number beside the sentence it came from.

    In testing the model turned 'we lost 14000 gallons' into 'saving 14000
    gallons'. Nothing short of a much larger model reliably prevents that, so
    the next best thing is to put the two lines next to each other where a
    reversal is obvious at a glance.
    """
    bare = {n.replace(",", ""): n for n in re.findall(r"\b\d[\d,]*\b", text)}
    kept = [(n, bare[n.replace(",", "")]) for n in re.findall(r"\b\d[\d,]{1,}\b", doc)
            if n.replace(",", "") in bare]
    shown = 0
    out = []
    for n, as_said in dict.fromkeys(kept):
        said = sentence_with(as_said, text)
        wrote = next((" ".join(l.split()) for l in doc.splitlines()
                      if re.search(rf"\b{re.escape(n)}\b", l)), None)
        if not said or not wrote:
            continue
        out.append((n, said, wrote))
        shown += 1
        if shown >= 6:
            break
    if not out:
        return
    print("\nCheck these numbers didn't get turned around.")
    print("A loss written as a saving is the error to look for:")
    for n, said, wrote in out:
        print(f"\n  {n}")
        print(f"      you said: {said}")
        print(f"      it wrote: {wrote}")


def run(model, text, ctx):
    req = urllib.request.Request(
        f"{HOST}/api/chat",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": PROMPT + text}],
            "stream": False,
            "options": {"num_ctx": ctx, "temperature": 0.2},
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=1800) as r:
            out = json.load(r)["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode(errors="replace")
        log(f"HTTP {e.code} from ollama: {body}")
        sys.exit(
            f"Ollama rejected the request (HTTP {e.code}).\n{body}\n\n"
            "If it mentions memory, the model is too big for this card. Try:\n"
            "    ollama pull qwen3:8b\n"
            "then run this again."
        )
    except urllib.error.URLError as e:
        log(f"URLError talking to ollama: {e.reason}")
        sys.exit(
            f"Lost the connection to Ollama: {e.reason}\n"
            "Start the Ollama app from the Start menu, then run this again."
        )
    log(f"generated {len(out)} chars in {time.time() - started:.0f}s")
    return out


def pick_model():
    """Prefer a model that fits a 12GB card and follows instructions well."""
    try:
        with urllib.request.urlopen(f"{HOST}/api/tags", timeout=10) as r:
            have = [m["name"] for m in json.load(r).get("models", [])]
    except Exception:
        sys.exit(
            "Can't reach Ollama at " + HOST + "\n"
            "Start it first — on Windows, run the Ollama app from the Start menu."
        )
    if not have:
        sys.exit("Ollama is running but has no models.\n  Fix:  ollama pull qwen2.5:14b")
    for want in ("qwen3:14b", "qwen2.5:14b", "qwen3:8b", "gemma3:12b", "qwen2.5:latest"):
        for h in have:
            if h.startswith(want):
                return h
    return have[0]


def main():
    global LOG

    args = [a for a in sys.argv[1:]]
    if "--log" in args:
        args.remove("--log")
        LOG = ROOT / "logs" / "profile-build.log"
        LOG.parent.mkdir(parents=True, exist_ok=True)
        log("=== extract_profile ===")

    model_override = None
    if "--model" in args:
        i = args.index("--model")
        try:
            model_override = args[i + 1]
            del args[i:i + 2]
        except IndexError:
            sys.exit("--model needs a model name after it")

    if not args:
        sys.exit(__doc__)

    src = Path(args[0]).expanduser()
    if not src.exists():
        log(f"input missing: {src}")
        sys.exit(f"No such file: {src}")

    log(f"input: {src.name} ({src.stat().st_size} bytes)")
    text = load_interview(src)
    words = len(text.split())
    log(f"words: {words}")

    if words < 50:
        sys.exit(
            f"{src} only has {words} words in it.\n"
            "That's too short to build a profile from — go back and keep talking."
        )

    model = model_override or pick_model()
    log(f"model: {model}")
    print(f"Model: {model}")
    print(f"Interview: {words:,} words")
    print("Writing the profile. On a 12GB card this takes a few minutes.\n")

    doc = run(model, text, 32768)
    doc = re.sub(r"^```(?:markdown)?\n|\n```$", "", doc.strip())

    if OUT.exists():
        backup = OUT.with_suffix(".md.previous")
        backup.write_text(OUT.read_text())
        print(f"Your old profile was saved to {backup}\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc + "\n")
    print(f"Wrote {OUT}\n")

    # ── The review list. This is the part that makes it safe to use. ──────
    print("=" * 68)
    print("NOW READ IT. The model gets small things wrong.")
    print("=" * 68)

    log(f"profile written: {len(doc)} chars, {len(doc.splitlines())} lines")

    flags = re.findall(r"\[(?:FLAG|DO NOT CLAIM)[^\]]*\]", doc)
    if flags:
        print(f"\n{len(flags)} thing(s) it knew it didn't know — fill these in:")
        for f in dict.fromkeys(flags):
            print("   ", f)

    # The model is inconsistent about the italic markers, so matching only
    # "*Title* | dates" silently skipped this entire check in testing. Match
    # any "something | something" line that isn't a markdown table row.
    titles = [
        m.strip().strip("*")
        for m in re.findall(r"^\s*\*?([^|\n#>-][^|\n]*?)\*?\s*\|", doc, re.M)
        if not m.strip().startswith("|")
    ]
    if titles:
        print("\nJob titles it wrote. Did you actually say each of these?")
        for ti in titles:
            print("   ", ti)

    def norm(n):
        return n.replace(",", "")

    nums_doc = {norm(n) for n in re.findall(r"\b\d[\d,]*\b", doc)}
    src_seen = {}
    for n in re.findall(r"\b\d[\d,]*\b", text):
        src_seen.setdefault(norm(n), n)
    dropped = sorted((o for k, o in src_seen.items() if k not in nums_doc),
                     key=len, reverse=True)[:8]
    if dropped:
        print("\nNumbers you said that did NOT make it in. Add any that matter:")
        print("   ", ", ".join(dropped))

    check_denials(doc, text)
    check_directions(doc, text)

    print("\nThen open the file and fix anything wrong:")
    print(f"    {OUT}")

    # Counts, not contents: enough to tell whether the model behaved, without
    # putting a single line of this person's career into a shareable log.
    log(f"review: {len(flags)} flags, {len(titles)} titles written, "
        f"{len(dropped)} numbers dropped")


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        # sys.exit with a message is a handled error; record the code only.
        log(f"exit: {e.code if isinstance(e.code, int) else 1}")
        raise
    except Exception:
        # A traceback is the single most useful thing in a bug report, and the
        # one thing a non-technical user will never think to copy down.
        log("CRASH\n" + traceback.format_exc())
        print("\n" + "=" * 68)
        print("This crashed. The details were saved to logs/profile-build.log")
        print("Double-click 'Share My Log.bat' and send the file.")
        print("=" * 68 + "\n")
        traceback.print_exc()
        sys.exit(1)
