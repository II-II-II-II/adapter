#!/usr/bin/env python3
"""
Pipeline dashboard — one view of the whole job search.

    python3 source/pipeline.py            # full dashboard
    python3 source/pipeline.py --brief    # just the live processes + calendar
    python3 source/pipeline.py --plain    # no ANSI colour (for piping/MCP)

Reads APPLICATIONS.md and INTERVIEWS.md. Those markdown files stay the source
of truth — this only renders them, so nothing has to be kept in sync by hand.
"""
import os
import argparse
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Filename prefix for generated documents, e.g. "Smith_" -> Smith_Acme_Role.pdf.
# Set to "" for no prefix.
DOC_PREFIX = os.environ.get("ADAPTER_DOC_PREFIX", "")
TRACKER = ROOT / "APPLICATIONS.md"
INTERVIEWS = ROOT / "INTERVIEWS.md"
REGISTRY = ROOT / "source" / "jd_registry.yaml"

C = {"hdr": "\033[1;36m", "ok": "\033[32m", "warn": "\033[33m", "bad": "\033[31m",
     "dim": "\033[2m", "bold": "\033[1m", "off": "\033[0m"}


def paint(s, key, on=True):
    return f"{C[key]}{s}{C['off']}" if on else s


def clean(s):
    """Strip markdown emphasis, links and strikethrough down to plain text."""
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s or "")
    s = re.sub(r"[*~`]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def first_url(s):
    """Pull the JD link out of a cell before clean() flattens it away."""
    m = re.search(r"\]\((https?://[^)]+)\)", s or "")
    return m.group(1) if m else None


def sections(text):
    """Split a markdown doc into {heading: body} on ## headers."""
    out, cur, buf = {}, "_preamble", []
    for line in text.splitlines():
        if line.startswith("## "):
            out[cur] = "\n".join(buf)
            cur, buf = clean(line[3:]), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def rows(body):
    """Yield table rows as lists of cells, plus any JD link found in the row.

    Yields (cells, url). The URL is captured from the raw markdown before clean()
    flattens links to plain text, so the dashboard can make the role clickable.
    """
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        raw = line.strip("|").split("|")
        cells = [clean(c) for c in raw]
        if cells and cells[0].lower() in ("date", "company", "when", "what"):
            continue
        if len(cells) >= 2:
            url = next((u for u in (first_url(c) for c in raw) if u), None)
            yield cells, url


DEAD = re.compile(r"❌|REJECTED|DEAD|filled it (internally|on their own)|declined for this role", re.I)
SENT = re.compile(r"\bSubmitted\b|Sent to recruiter|→ Moved to In Flight", re.I)
# "Built <date>" leads almost every row as a normal authoring convention, so a bare
# \bBuilt\b filed 24 SENT applications as never-submitted and wrecked the funnel math.
# Only count a row as unsent when it says so explicitly. Found 2026-09-10.
BUILT = re.compile(r"ready to send|not (yet )?submitted|built,? not sent|NOT SENT", re.I)
LIVE = re.compile(r"🎉|Interview|Round \d|CONFIRMED|scheduled|In conversation|Waiting on|advocating", re.I)
MONEY = re.compile(r"\$\s?(\d{2,3}),?(\d{3})")
# "$150K" is as common in these notes as "$150,000" and was silently unparsed,
# which made every K-denominated row look like it had no comp at all.
MONEY_K = re.compile(r"\$\s?(\d{2,3})\s?K\b", re.I)


def top_comp(s):
    text = s or ""
    vals = [int(a + b) for a, b in MONEY.findall(text)]
    vals += [int(m) * 1000 for m in MONEY_K.findall(text)]
    return max(vals) if vals else None


def key(name):
    """Normalize a company name for matching across tables."""
    return re.sub(r"[^a-z0-9]", "", (name or "").split("(")[0].lower())


def funnel(apps, inflight):
    """Conversion math.

    An application 'converted' if that company shows up in the live-conversation
    table. Rate is measured against applications that have actually RESOLVED —
    something still awaiting a reply is not a failure yet, and parking it in the
    denominator makes the number look worse than reality every time you apply.
    """
    # "Converted" means the application EVER produced a human conversation —
    # a company in the In-flight table, whether that conversation is still live
    # or has since died. A process that went four rounds before ending is a hit
    # that later failed, not a non-hit.
    #
    # The old math counted the same rows as converted but then EXCLUDED them
    # from `rejected`, so the losses vanished from the denominator entirely and
    # the rate read roughly double the truth. Rejections now count every dead
    # row that never produced a conversation.
    ever_talked = {key(r["company"]) for r in inflight}
    still_live = {key(r["company"]) for r in inflight
                  if classify(r["status"]) != "dead"}
    converted = [a for a in apps if key(a["company"]) in ever_talked]
    rejected = [a for a in apps if effective(a, inflight) == "dead"
                and key(a["company"]) not in ever_talked]
    # Silence IS an answer. An application sent 3+ weeks ago with no reply is a
    # rejection, not an open question — leaving those in "pending" forever kept
    # them out of the denominator and flattered the rate badly.
    def age_days(a):
        try:
            d = datetime.strptime(f"{a.get('date','')} {datetime.now().year}", "%b %d %Y")
            return (datetime.now() - d).days
        except ValueError:
            return 0

    STALE = 21
    open_sent = [a for a in apps if effective(a, inflight) in ("sent", "unknown")
                 and key(a["company"]) not in ever_talked]
    ghosted = [a for a in open_sent if age_days(a) >= STALE]
    pending = [a for a in open_sent if age_days(a) < STALE]
    rejected = rejected + ghosted
    resolved = len(converted) + len(rejected)
    return {
        "total": len(apps), "converted": len(converted), "rejected": len(rejected),
        "pending": len(pending), "resolved": resolved, "live": len(still_live),
        "rate": (len(converted) / resolved * 100) if resolved else 0.0,
        "raw_rate": (len(converted) / len(apps) * 100) if apps else 0.0,
    }


def effective(a, inflight):
    """classify() the application row, but let the In-flight table override it.

    The DEAD marker for a company that reached interviews lives on its In-flight
    row, not on its original application row — so companies that had clearly been
    lost kept rendering as "awaiting reply" for weeks afterward. The In-flight
    table is the authority on a company's real state. Added 2026-09-10.
    """
    k = key(a["company"])
    for r in inflight:
        if key(r["company"]) == k:
            st = classify(r["status"])
            return "dead" if st == "dead" else ("live" if st == "live" else
                                                classify(a["status"]))
    return classify(a["status"])


def classify(status):
    """Classify a row from the state marker that LEADS the status cell.

    Everything after that marker is commentary, and commentary routinely
    mentions interviews, rounds and scheduling for other reasons — a note
    reading "Submitted... confirm before interviewing" is submitted, not live.
    Matching the whole cell filed four sent applications as live conversations.
    """
    head = status.strip()[:90]
    if DEAD.search(head):
        return "dead"
    if BUILT.search(head) and not SENT.search(head):
        return "built"
    if SENT.search(head):
        return "sent"
    if LIVE.search(head):
        return "live"
    if head.startswith("?"):
        return "unknown"
    return "sent"


def registry():
    """company-key -> {jd, docs, role}. Optional; absent file just means no links."""
    try:
        import yaml
    except ImportError:
        return {}
    if not REGISTRY.exists():
        return {}
    data = yaml.safe_load(REGISTRY.read_text()) or {}
    out = {}
    for group in ("applications", "not_submitted"):
        for e in data.get(group) or []:
            out.setdefault(key(e.get("match", "")), e)
    return out


def doc_links(stem):
    """Return (resume_url, letter_url) as file:// links when the files exist."""
    if not stem:
        return None, None
    r = ROOT / "output" / "resumes" / f"{DOC_PREFIX}{stem}.pdf"
    c = ROOT / "output" / "cover_letters" / f"{DOC_PREFIX}{stem}_CoverLetter.pdf"
    return (r.as_uri() if r.exists() else None, c.as_uri() if c.exists() else None)


def load():
    tracker = sections(TRACKER.read_text()) if TRACKER.exists() else {}
    reg = registry()
    apps, inflight, contract, dead = [], [], [], []
    for head, body in tracker.items():
        low = head.lower()
        for cells, url in rows(body):
            if "in flight" in low and len(cells) >= 4:
                inflight.append({"company": cells[0], "role": cells[1],
                                 "comp": cells[2], "status": cells[3], "url": url})
            elif "contract" in low and len(cells) >= 3:
                contract.append({"when": cells[0], "what": cells[1],
                                 "who": cells[2], "status": cells[-1], "url": url})
            elif "not pursued" in low and len(cells) >= 3:
                dead.append({"date": cells[0], "company": cells[1],
                             "role": cells[2], "why": cells[-1], "url": url})
            elif len(cells) >= 7:
                apps.append({"date": cells[0], "company": cells[1], "role": cells[2],
                             "loc": cells[3], "comp": cells[4], "docs": cells[5],
                             "status": cells[6], "url": url})
    for row in apps + inflight:
        e = reg.get(key(row["company"])) or {}
        row["url"] = row.get("url") or e.get("jd")
        row["resume"], row["letter"] = doc_links(e.get("docs"))

    cal = []
    if INTERVIEWS.exists():
        for head, body in sections(INTERVIEWS.read_text()).items():
            if "calendar" in head.lower():
                for cells, _ in rows(body):
                    if len(cells) >= 3:
                        cal.append({"when": cells[0], "what": cells[1], "who": cells[2]})
    return apps, inflight, contract, dead, cal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--html", metavar="PATH", help="write a self-contained HTML dashboard")
    ap.add_argument("--serve", nargs="?", const=8765, type=int, metavar="PORT",
                    help="serve the dashboard at localhost:PORT (default 8765)")
    args = ap.parse_args()
    if args.serve:
        serve(args.serve)
        return
    if args.html:
        print(f'Wrote {render_html(args.html)}')
        return
    col = not args.plain

    apps, inflight, contract, dead_tbl, cal = load()
    buckets = {}
    for a in apps:
        buckets.setdefault(effective(a, inflight), []).append(a)

    W = 96
    print()
    print(paint("═" * W, "hdr", col))
    print(paint(f"  PIPELINE — {datetime.now():%a %b %d, %Y}", "bold", col))
    print(paint("═" * W, "hdr", col))

    # An "In flight" row can be dead (req filled) or deliberately parked
    # (below comp floor, wrong use case). Counting those as live overstates
    # the pipeline, which is the exact thing this dashboard exists to prevent.
    COLD = re.compile(r"LOW PRIORITY|Deprioritize|below (Ian's )?\$?\d*K? ?floor|last ditch", re.I)
    FLOOR = 145_000

    def is_cold(r):
        blob = f"{r['comp']} {r['status']}"
        if COLD.search(blob):
            return True
        ceiling = top_comp(r["comp"])          # top of the posted band
        return ceiling is not None and ceiling < FLOOR

    # Match the state marker that LEADS the cell, same rule classify() uses.
    # Searching the whole cell mis-killed a live row on the word "rejected" inside
    # "will state a reason if rejected" — commentary, not status.
    def is_dead(r):
        return bool(DEAD.search(r["status"].strip()[:90]))

    hot = [r for r in inflight if not is_dead(r) and not is_cold(r)]
    warm = [r for r in inflight if r not in hot and not is_dead(r)]
    gone = [r for r in inflight if is_dead(r)]

    print(f"\n  {paint('LIVE CONVERSATIONS', 'bold', col)} ({len(hot)})")
    for r in hot:
        print(f"   {paint('●', 'ok', col)} {paint(r['company'], 'bold', col)} — {r['role'][:62]}")
        if r["comp"] and r["comp"] not in ("-", "—"):
            print(f"       {paint('comp:', 'dim', col)} {r['comp'][:86]}")
        print(f"       {r['status'][:200]}")

    if warm:
        print(f"\n  {paint('PARKED — live but deprioritized', 'bold', col)} ({len(warm)})")
        for r in warm:
            why = "below floor" if re.search(r"floor|\$1[0-4]\d", r["comp"] + r["status"], re.I) else "deprioritized"
            print(f"   {paint('◐', 'warn', col)} {r['company'][:26]:28} {r['role'][:40]:42} {why}")

    if gone:
        print(f"\n  {paint('WAS LIVE — now closed', 'bold', col)} ({len(gone)})")
        for r in gone:
            print(f"   {paint('✗', 'bad', col)} {r['company'][:26]:28} {r['status'][:60]}")

    if cal:
        print(f"\n  {paint('CALENDAR', 'bold', col)}")
        for c in cal:
            done = c["when"].startswith("✅")
            mark = paint("✓", "dim", col) if done else paint("▶", "warn", col)
            print(f"   {mark} {c['when'][:34]:36} {c['what'][:52]}")

    if args.brief:
        print()
        return

    order = [("live", "IN PROCESS", "ok"), ("built", "BUILT — NOT SENT", "warn"),
             ("sent", "SUBMITTED — AWAITING", "dim"), ("unknown", "STATUS UNKNOWN", "warn"),
             ("dead", "CLOSED", "bad")]
    for key, label, colr in order:
        items = buckets.get(key, [])
        if not items:
            continue
        print(f"\n  {paint(label, 'bold', col)} ({len(items)})")
        for a in items:
            money = top_comp(a["comp"])
            m = f"${money//1000}K" if money else "—"
            print(f"   {paint('•', colr, col)} {a['company'][:26]:28} {a['role'][:44]:46} {m:>7}  {a['date']}")

    f = funnel(apps, inflight)
    bar_w = 46
    filled = round(f["raw_rate"] / 100 * bar_w)
    print(f"\n  {paint('CONVERSION', 'bold', col)}")
    print(f"   {paint('█' * filled, 'ok', col)}{paint('░' * (bar_w - filled), 'dim', col)}  "
          f"{paint(f'{f['raw_rate']:.0f}%', 'bold', col)}")
    print(f"   {f['converted']} of {f['total']} logged applications ever became a conversation")
    print(paint(f"   {f['rate']:.0f}% of the {f['resolved']} that have resolved · "
                f"{f['rejected']} rejected or gone quiet 21+ days · "
                f"{f['pending']} still genuinely open", "dim", col))
    print(paint("   ⚠ Most conversations came from warm channels, not cold applications — "
                "see the round-loss table in APPLICATIONS.md.", "dim", col))

    if contract:
        print(f"\n  {paint('CONTRACT / CONSULTING TRACK', 'bold', col)}")
        for c in contract:
            print(f"   • {c['when'][:22]:24} {c['what'][:60]}")

    if dead_tbl:
        print(f"\n  {paint('NOT PURSUED / CLOSED', 'bold', col)} ({len(dead_tbl)}) "
              f"{paint('— most recent first', 'dim', col)}")
        for d in dead_tbl[:8]:
            print(f"   {paint('✗', 'bad', col)} {d['company'][:24]:26} {d['role'][:40]:42} {d['why'][:44]}")

    tot = len(apps)
    live = len(buckets.get("live", [])) + sum(
        1 for r in inflight if not DEAD.search(r["status"].strip()[:90]))
    print()
    print(paint("─" * W, "dim", col))
    print(f"  {tot} applications logged · {paint(str(live), 'ok', col)} live · "
          f"{len(buckets.get('built', []))} built not sent · "
          f"{len(buckets.get('sent', []))} awaiting · "
          f"{paint(str(len(buckets.get('dead', [])) + len(dead_tbl)), 'bad', col)} closed")
    print(paint("─" * W, "dim", col))
    print()




# ---------------------------------------------------------------- HTML export

HTML_CSS = """
:root{--ground:#FAFAF8;--surface:#FFF;--raise:#F2F2EE;--ink:#16191D;--muted:#5B6470;
--line:#E4E4DF;--accent:#0F766E;--accent-soft:#D5E8E5;--live:#15803D;--warn:#B45309;--dead:#9F1239;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#111417;--surface:#181C20;
--raise:#1F242A;--ink:#E8E9E6;--muted:#98A1AC;--line:#2A3037;--accent:#4DB6AC;--accent-soft:#1B3B38;
--live:#4ADE80;--warn:#FBBF24;--dead:#FB7185;}}
:root[data-theme="dark"]{--ground:#111417;--surface:#181C20;--raise:#1F242A;--ink:#E8E9E6;
--muted:#98A1AC;--line:#2A3037;--accent:#4DB6AC;--accent-soft:#1B3B38;--live:#4ADE80;
--warn:#FBBF24;--dead:#FB7185;}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);margin:0;padding:32px 20px 64px;
font:15px/1.55 ui-sans-serif,-apple-system,"Segoe UI",system-ui,sans-serif;}
.wrap{max-width:1080px;margin:0 auto;display:flex;flex-direction:column;gap:34px}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}
h1{font-size:26px;margin:0;letter-spacing:-.02em;text-wrap:balance}
.stamp{color:var(--muted);font-size:12.5px;letter-spacing:.09em;text-transform:uppercase}
h2{font-size:12.5px;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);
margin:0 0 12px;font-weight:650}
.bar{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:1px;
background:var(--line);border:1px solid var(--line);border-radius:3px;overflow:hidden}
.stat{background:var(--surface);padding:14px 16px}
.stat .n{font-size:27px;font-weight:660;letter-spacing:-.02em;display:block}
.stat .l{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.cards{display:flex;flex-direction:column;gap:10px}
.card{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--live);
border-radius:3px;padding:14px 16px;display:flex;flex-direction:column;gap:5px}
.card.warn{border-left-color:var(--warn)} .card.dead{border-left-color:var(--dead)}
.card .top{display:flex;justify-content:space-between;gap:14px;align-items:baseline;flex-wrap:wrap}
.co{font-weight:660;font-size:16px}
.role{color:var(--muted);font-size:13.5px}
.money{font-size:13px;font-weight:640;color:var(--accent);white-space:nowrap}
.note{font-size:13px;color:var(--muted);line-height:1.5}
.pill{display:inline-block;font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
padding:2px 7px;border-radius:2px;background:var(--accent-soft);color:var(--accent);font-weight:640}
table{width:100%;border-collapse:collapse;font-size:13.5px}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--surface)}
th{text-align:left;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
padding:9px 14px;border-bottom:1px solid var(--line);font-weight:640;white-space:nowrap}
td{padding:9px 14px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td.r{text-align:right;white-space:nowrap}
.dim{color:var(--muted)}
.conv{background:var(--surface);border:1px solid var(--line);border-radius:3px;
padding:18px 20px;display:flex;gap:22px;align-items:flex-start;flex-wrap:wrap}
.conv .big{font-size:52px;font-weight:680;letter-spacing:-.03em;line-height:1;color:var(--accent)}
.conv .pc{font-size:24px;font-weight:600;margin-left:2px}
.convtxt{flex:1;min-width:240px;display:flex;flex-direction:column;gap:7px}
.convlead{font-size:15px;font-weight:600}
.convsub{font-size:12.5px;color:var(--muted)}
.big-track{height:8px}
.ladder{display:flex;flex-direction:column;gap:7px}
.rung{display:grid;grid-template-columns:190px 1fr 58px;gap:12px;align-items:center;font-size:13.5px}
.track{background:var(--raise);border-radius:2px;height:19px;position:relative;overflow:hidden}
.fill{background:var(--accent);height:100%;border-radius:2px;opacity:.82}
.rung .lbl{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tl{display:flex;flex-direction:column;gap:0;border-left:2px solid var(--line);padding-left:16px}
.ev{padding:7px 0;display:flex;gap:12px;align-items:baseline;position:relative}
.ev::before{content:"";position:absolute;left:-21px;top:13px;width:8px;height:8px;border-radius:50%;
background:var(--warn);border:2px solid var(--ground)}
.ev.done::before{background:var(--line)}
.ev.done{color:var(--muted)}
.when{font-size:12.5px;min-width:190px;font-weight:600}
.what{font-size:13.5px}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:3px}
.chip{font-size:11px;letter-spacing:.04em;padding:3px 8px;border-radius:2px;
border:1px solid var(--line);color:var(--muted);text-decoration:none;white-space:nowrap}
.chip:hover,.chip:focus{border-color:var(--accent);color:var(--accent)}
a{color:var(--accent);text-decoration:none}
a:hover,a:focus{text-decoration:underline}
a:focus-visible,.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media(max-width:620px){
 body{padding:20px 12px 48px;font-size:14.5px}
 .wrap{gap:26px}
 h1{font-size:22px}
 .bar{grid-template-columns:repeat(2,1fr)}
 .stat .n{font-size:22px}
 .conv{padding:14px;gap:14px}
 .conv .big{font-size:40px}
 .when{min-width:0}
 .ev{flex-direction:column;gap:2px}
 .card .top{flex-direction:column;gap:2px}
 .chip{padding:6px 10px;font-size:12px}          /* touch target */
 /* stack table rows into records — horizontal scroll is unusable on a phone */
 .scroll{border:none;background:none}
 table,tbody,tr,td{display:block;width:100%}
 thead{display:none}
 tr{background:var(--surface);border:1px solid var(--line);border-radius:3px;
    padding:10px 12px;margin-bottom:8px}
 td{border:none;padding:2px 0;display:flex;gap:10px;justify-content:space-between}
 td::before{content:attr(data-label);color:var(--muted);font-size:11px;
   letter-spacing:.07em;text-transform:uppercase;flex:0 0 auto;padding-top:2px}
 td.r{text-align:left}
}
"""


def chips(row):
    """Small link row: job description, resume, cover letter — whichever exist."""
    out = []
    for label, u in (("Job description \u2197", row.get("url")),
                     ("Resume", row.get("resume")), ("Cover letter", row.get("letter"))):
        if u:
            out.append(f'<a class="chip" href="{esc(u)}" target="_blank" rel="noopener">{label}</a>')
    return f'<div class="chips">{"".join(out)}</div>' if out else ""


def link(text, url):
    """Render a role as a clickable JD link when we captured one."""
    t = esc(text)
    return (f'<a href="{esc(url)}" target="_blank" rel="noopener">{t} \u2197</a>'
            if url else t)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_html():
    apps, inflight, contract, dead_tbl, cal = load()
    COLD = re.compile(r"LOW PRIORITY|Deprioritize|below (Ian's )?\$?\d*K? ?floor|last ditch", re.I)

    def cold(r):
        if COLD.search(f"{r['comp']} {r['status']}"):
            return True
        c = top_comp(r["comp"])
        return c is not None and c < 145_000

    hot = [r for r in inflight
           if not DEAD.search(r["status"].strip()[:90]) and not cold(r)]
    warm = [r for r in inflight
            if r not in hot and not DEAD.search(r["status"].strip()[:90])]
    buckets = {}
    for a in apps:
        buckets.setdefault(effective(a, inflight), []).append(a)
    built, awaiting = buckets.get("built", []), buckets.get("sent", [])
    closed = buckets.get("dead", []) + dead_tbl

    f = funnel(apps, inflight)

    h = [f"<title>Pipeline — {datetime.now():%b %d}</title>", f"<style>{HTML_CSS}</style>",
         '<div class="wrap">',
         f'<header><div class="stamp mono">Job search · updated {datetime.now():%a %b %d, %Y}</div>'
         f'<h1>Pipeline</h1></header>',
         '<div class="bar">',
         f'<div class="stat"><span class="n mono">{len(hot)}</span><span class="l">Live</span></div>',
         f'<div class="stat"><span class="n mono">{len(built)}</span><span class="l">Built, unsent</span></div>',
         f'<div class="stat"><span class="n mono">{len(awaiting)}</span><span class="l">Awaiting</span></div>',
         f'<div class="stat"><span class="n mono">{len(warm)}</span><span class="l">Parked</span></div>',
         f'<div class="stat"><span class="n mono">{len(closed)}</span><span class="l">Closed</span></div>',
         '</div>']

    h.append('<section><h2>Live conversations</h2><div class="cards">')
    for r in hot:
        role = esc(r["role"])
        if r.get("url"):
            role = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener">{role} \u2197</a>'
        h.append(f'<article class="card"><div class="top"><span class="co">{esc(r["company"])}</span>'
                 f'<span class="money mono">{esc(r["comp"][:44])}</span></div>'
                 f'<div class="role">{role}</div>'
                 f'<div class="note">{esc(r["status"][:260])}</div>'
                 f'{chips(r)}</article>')
    h.append("</div></section>")

    if cal:
        h.append('<section><h2>Calendar</h2><div class="tl">')
        for c in cal:
            done = "done" if c["when"].startswith("✅") else ""
            h.append(f'<div class="ev {done}"><span class="when mono">{esc(c["when"])}</span>'
                     f'<span class="what">{esc(c["what"])}</span></div>')
        h.append("</div></section>")

    # Headline the RAW rate. Showing only "of resolved" hides every silent
    # rejection and roughly doubles the apparent hit rate.
    pct = round(f["raw_rate"])
    h.append(
        '<section><h2>Conversion</h2><div class="conv">'
        f'<div class="big mono">{pct}<span class="pc">%</span></div>'
        '<div class="convtxt">'
        f'<div class="convlead">of all {f["total"]} logged applications ever became '
        'a conversation</div>'
        f'<div class="convsub mono">{f["converted"]} converted &middot; '
        f'{f["rejected"]} rejected or silent 21+ days &middot; '
        f'{f["pending"]} genuinely still open &middot; '
        f'{round(f["rate"])}% of the {f["resolved"]} resolved</div>'
        '<div class="track big-track">'
        f'<span class="fill" style="width:{max(3, pct)}%"></span></div>'
        '<div class="convsub dim">Silence past 21 days counts as a no. '
        '⚠ Count how many of these came from a cold application versus a '
        'recruiter, referral or inbound interest — the two rates are usually '
        'very different, and only the cold one tells you whether applying '
        'is working.</div>'
        '</div></div></section>')

    def table(title, items, cols, rowfn):
        if not items:
            return
        h.append(f'<section><h2>{title} ({len(items)})</h2><div class="scroll"><table><thead><tr>'
                 + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>")
        for it in items:
            # Tag each cell with its column name so the mobile stylesheet can stack
            # rows into labelled records — horizontal scroll is unusable on a phone.
            n = iter(cols)
            cells = re.sub(r"<td(?=[ >])",
                           lambda _m: f'<td data-label="{next(n, "")}"', rowfn(it))
            h.append("<tr>" + cells + "</tr>")
        h.append("</tbody></table></div></section>")

    table("Built — not sent", built, ["Company", "Role", "Comp", "Built"],
          lambda a: f'<td><strong>{esc(a["company"])}</strong></td><td>{link(a["role"], a.get("url"))}</td>'
                    f'<td class="r money mono">{("$"+str(top_comp(a["comp"])//1000)+"K") if top_comp(a["comp"]) else "—"}</td>'
                    f'<td class="r dim mono">{esc(a["date"])}</td>')
    table("Submitted — awaiting reply", awaiting, ["Company", "Role", "Comp", "Sent"],
          lambda a: f'<td>{esc(a["company"])}</td><td class="dim">{link(a["role"], a.get("url"))}</td>'
                    f'<td class="r mono">{("$"+str(top_comp(a["comp"])//1000)+"K") if top_comp(a["comp"]) else "—"}</td>'
                    f'<td class="r dim mono">{esc(a["date"])}</td>')
    table("Parked — below floor or deprioritized", warm, ["Company", "Role", "Comp"],
          lambda r: f'<td>{esc(r["company"])}</td><td class="dim">{link(r["role"], r.get("url"))}</td>'
                    f'<td class="r mono dim">{esc(r["comp"][:34])}</td>')
    table("Closed", closed, ["Company", "Role / Why"],
          lambda a: f'<td class="dim">{esc(a.get("company",""))}</td>'
                    f'<td class="dim">{esc((a.get("role") or "")+" — "+(a.get("why") or a.get("status",""))[:110])}</td>')

    h.append("</div>")
    return "\n".join(h)


def render_html(path):
    Path(path).write_text(build_html(), encoding="utf-8")
    return path


def serve(port):
    """Serve the dashboard on localhost.

    Re-reads APPLICATIONS.md and INTERVIEWS.md on every request, so the page is
    current the moment the tracker changes — there is no regeneration step to
    forget. Bound to 127.0.0.1 only; this is personal data.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.split("?")[0] not in ("/", "/index.html"):
                self.send_error(404)
                return
            try:
                page = (
                    "<!doctype html><meta charset='utf-8'>"
                    "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                    + build_html()
                )
            except Exception as exc:  # noqa: BLE001 - surface it in the browser
                page = f"<pre>dashboard error: {exc}</pre>"
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    import socket
    lan = "?"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))          # no packet sent; just resolves the local iface
        lan, _ = s.getsockname()
        s.close()
    except OSError:
        pass

    # Bound to 0.0.0.0 so other devices on the LAN can reach it. There is no auth —
    # anything on the same Wi-Fi can read the whole tracker. Fine on a home network,
    # not on a shared one.
    srv = HTTPServer(("0.0.0.0", port), Handler)
    print(f"\n  Pipeline dashboard")
    print(f"    this machine   →  http://localhost:{port}")
    print(f"    phone / laptop →  http://{lan}:{port}")
    print("\n  Live from APPLICATIONS.md + INTERVIEWS.md. Refresh to update. Ctrl-C to stop.")
    print("  Note: no password — anyone on this Wi-Fi can open it.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("  stopped\n")


if __name__ == "__main__":
    main()
