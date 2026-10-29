#!/usr/bin/env python3
"""
Job Search MCP Server
=====================

Exposes Ian's job-search workspace to any MCP-compatible client (Claude Code,
Claude Desktop, Cursor, etc.) over stdio.

Design notes — the interesting decisions are about ACCESS, not code:

  * The server is READ-ONLY over the tracker and profile. It has no tool that
    writes or deletes. A compromised or confused client cannot mutate state.

  * `get_profile` REDACTS sections marked [PRIVATE — DO NOT USE EXTERNALLY]
    and [INTERVIEW-ONLY ...] before returning anything. The filtering happens
    at the server boundary, not in the client's prompt — we do not trust the
    caller to behave.

  * `run_job_scan` is the only tool with side effects. It makes outbound calls
    to ~46 external job boards, so it is bounded by a hard timeout and returns
    a summary rather than dumping raw results into the context window.

Run directly for a smoke test:   python3 source/mcp_server.py --selftest
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from mcp.server import MCPServer

ROOT = Path(__file__).resolve().parent.parent
SCOUT_DIR = ROOT / "output" / "scout"
TRACKER = ROOT / "APPLICATIONS.md"
PROFILE = ROOT / "source" / "master_profile.md"
SCOUT_SCRIPT = ROOT / "source" / "job_scout.py"

SCAN_TIMEOUT_SECONDS = 180

mcp = MCPServer("job-search")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def _latest_shortlists(limit: int = 3) -> list[Path]:
    if not SCOUT_DIR.exists():
        return []
    return sorted(SCOUT_DIR.glob("shortlist_*.md"), reverse=True)[:limit]


def _parse_shortlist(path: Path) -> list[dict]:
    """Turn a shortlist markdown file into structured job records."""
    jobs, current = [], None
    for line in path.read_text().splitlines():
        header = re.match(r"^### \[(\d+)\]\s+(.+?)\s+—\s+(.+)$", line)
        if header:
            if current:
                jobs.append(current)
            current = {
                "score": int(header.group(1)),
                "company": header.group(2).strip(),
                "title": header.group(3).strip(),
                "meta": "", "matched": "", "url": "", "source": path.name,
            }
            continue
        if current is None:
            continue
        if line.startswith("http"):
            current["url"] = line.strip()
        elif line.startswith("Matched:"):
            current["matched"] = line[len("Matched:"):].strip()
        elif line and not line.startswith(("#", ">", "-", "|")) and not current["meta"]:
            current["meta"] = line.strip()
    if current:
        jobs.append(current)
    return jobs


# --------------------------------------------------------------------------
# TOOLS
# --------------------------------------------------------------------------

@mcp.tool()
def search_jobs(query: str = "", min_score: int = 0, limit: int = 10) -> str:
    """Search recent job-scout shortlists.

    Args:
        query: case-insensitive text to match against company, title, or matched keywords.
               Leave empty to list everything.
        min_score: only return roles scoring at or above this value.
        limit: maximum results to return.
    """
    seen, results = set(), []
    for path in _latest_shortlists():
        for job in _parse_shortlist(path):
            key = job["url"] or f"{job['company']}|{job['title']}"
            if key in seen:
                continue
            seen.add(key)
            blob = f"{job['company']} {job['title']} {job['matched']}".lower()
            if query and query.lower() not in blob:
                continue
            if job["score"] < min_score:
                continue
            results.append(job)

    if not results:
        return "No matching roles found in the recent shortlists."

    results.sort(key=lambda j: -j["score"])
    out = [f"Found {len(results)} matching role(s); showing up to {limit}.", ""]
    for job in results[:limit]:
        out += [
            f"[{job['score']}] {job['company']} — {job['title']}",
            f"    {job['meta']}",
            f"    matched: {job['matched']}",
            f"    {job['url']}",
            "",
        ]
    return "\n".join(out)


@mcp.tool()
def get_pipeline() -> str:
    """Return the current job-search pipeline: roles with a live conversation,
    plus counts of everything submitted or passed on.

    Delegates to source/pipeline.py so the CLI dashboard and this tool can never
    disagree. Falls back to the original inline parse if that import fails.
    """
    if not TRACKER.exists():
        return "No tracker file found."

    try:
        import io
        import contextlib
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        import pipeline as _pipe
        buf = io.StringIO()
        argv = _sys.argv
        _sys.argv = ["pipeline.py", "--plain"]
        try:
            with contextlib.redirect_stdout(buf):
                _pipe.main()
        finally:
            _sys.argv = argv
        rendered = buf.getvalue().strip()
        if rendered:
            return rendered
    except Exception:  # noqa: BLE001 - fall through to the legacy parse
        pass

    text = TRACKER.read_text()
    in_flight, capturing = [], False
    for line in text.splitlines():
        if line.startswith("## ") and "In flight" in line:
            capturing = True
            continue
        if capturing and line.startswith("## "):
            break
        if capturing and line.startswith("|") and not re.match(r"^\|[\s\-|]+\|$", line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 4 and cells[0].lower() != "company":
                company = re.sub(r"\*\*", "", cells[0])
                status = re.sub(r"\*\*", "", cells[3])
                in_flight.append(f"  • {company} — {cells[1]}\n      comp: {cells[2]}\n      {status[:280]}")

    submitted = len(re.findall(r"^\| \w+ \d+ \|", text, re.M))
    out = [f"ACTIVE CONVERSATIONS ({len(in_flight)}):", ""]
    out += in_flight or ["  (none)"]
    out += ["", f"Total rows logged across submitted/passed tables: {submitted}"]
    return "\n".join(out)


@mcp.tool()
def run_job_scan(tag: str = "") -> str:
    """Run a live job scan across all watched company job boards.

    This has real side effects: it makes outbound HTTP requests to ~46 external
    ATS APIs and writes a new shortlist file. Bounded by a hard timeout.

    Args:
        tag: optionally restrict to one sector tag (e.g. 'iot', 'health-tech', 'space').
    """
    if not SCOUT_SCRIPT.exists():
        return "Scout script not found."

    cmd = [sys.executable, str(SCOUT_SCRIPT)]
    if tag:
        cmd += ["--tag", tag]
    try:
        proc = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True,
            timeout=SCAN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return (f"Scan exceeded the {SCAN_TIMEOUT_SECONDS}s timeout and was aborted. "
                "External job boards may be slow or rate-limiting.")

    if proc.returncode != 0:
        return f"Scan failed (exit {proc.returncode}):\n{proc.stderr[-500:]}"
    return proc.stdout.strip() or "Scan completed with no output."


@mcp.tool()
def check_gmail_messages(days: int = 30, limit: int = 25, query: str = "") -> str:
    """Read-only scan of recent Gmail messages — headers and snippet only,
    never full bodies. Requires a one-time browser consent already run via
    `python3 source/google_auth.py`.

    Args:
        days: how many days back to look (default 30).
        limit: maximum messages to return.
        query: raw Gmail search syntax, ANDed with the date window. Strongly
            preferred over scanning — e.g. "from:acme-corp.com",
            "subject:interview", "acme", "has:attachment". Without it you
            pull hundreds of unrelated messages and filter by eye.

    Drafts are flagged [DRAFT] and sent mail [SENT]. Gmail returns drafts
    alongside sent messages with an identical shape; never infer that something
    was sent just because it appears here.
    """
    try:
        from gmail_client import fetch_recent_messages
    except ImportError as e:
        return f"Gmail client dependencies missing: {e}"

    try:
        messages = fetch_recent_messages(days=days, max_results=limit, query=query)
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001 - surface auth/API errors as text, don't crash the server
        return f"Gmail fetch failed: {e}"

    scope = f"last {days} day(s)" + (f' matching "{query}"' if query else "")
    if not messages:
        return f"No messages found in the {scope}."

    out = [f"{len(messages)} message(s) from the {scope}:", ""]
    for m in messages:
        flag = " [DRAFT — NOT SENT]" if m.get("is_draft") else (" [SENT]" if m.get("is_sent") else "")
        out += [
            f"[id: {m['id']}]{flag}",
            f"From: {m['from']}",
            f"Subject: {m['subject']}",
            f"Date: {m['date']}",
            f"  {m['snippet']}",
            "",
        ]
    return "\n".join(out)


@mcp.tool()
def get_gmail_message(message_id: str) -> str:
    """Full body of one specific Gmail message, fetched on demand.

    Use this after `check_gmail_messages` to read one flagged message in
    full — pass the `id` shown next to it in that tool's output. Deliberately
    single-message, not a bulk fetch: the scan stays cheap, and a full body
    only gets pulled for something you've actually chosen to read.

    Args:
        message_id: the Gmail message id, as shown by check_gmail_messages.
    """
    try:
        from gmail_client import fetch_message_body
    except ImportError as e:
        return f"Gmail client dependencies missing: {e}"

    try:
        msg = fetch_message_body(message_id)
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001 - surface auth/API errors as text, don't crash the server
        return f"Gmail fetch failed: {e}"

    out = [
        f"From: {msg['from']}",
        f"To: {msg['to']}",
        f"Subject: {msg['subject']}",
        f"Date: {msg['date']}",
        "",
        msg["body"],
    ]
    if msg["truncated"]:
        out.append(f"\n[truncated at {6000} characters]")
    return "\n".join(out)


@mcp.tool()
def check_calendar(days_ahead: int = 14) -> str:
    """Read-only look at upcoming events on the primary Google Calendar —
    no create/edit/delete capability exists here or in the granted scope.

    Args:
        days_ahead: how many days out to look (default 14).
    """
    try:
        from calendar_client import fetch_upcoming_events
    except ImportError as e:
        return f"Calendar client dependencies missing: {e}"

    try:
        events = fetch_upcoming_events(days_ahead=days_ahead)
    except FileNotFoundError as e:
        return str(e)
    except Exception as e:  # noqa: BLE001 - surface auth/API errors as text, don't crash the server
        return f"Calendar fetch failed: {e}"

    if not events:
        return f"No events in the next {days_ahead} day(s)."

    out = [f"{len(events)} event(s) in the next {days_ahead} day(s):", ""]
    for ev in events:
        out += [f"{ev['start']} → {ev['end']}  |  {ev['summary']}"]
        if ev["location"]:
            out.append(f"    location: {ev['location']}")
        if ev["meeting_link"]:
            out.append(f"    link: {ev['meeting_link']}")
        if ev["attendees"]:
            out.append(f"    attendees: {', '.join(ev['attendees'])}")
        if ev["description"]:
            # invite bodies carry join links, agendas, and interviewer names —
            # dropping them silently is how a real invite looks empty
            body = "\n".join(f"      {line}" for line in ev["description"].splitlines())
            out.append("    details:")
            out.append(body)
        out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# RESOURCE  (read-only context, redacted at the boundary)
# --------------------------------------------------------------------------

PRIVATE_MARKERS = ("PRIVATE — DO NOT USE EXTERNALLY", "INTERVIEW-ONLY")


@mcp.resource("profile://master")
def get_profile() -> str:
    """Ian's master career profile, with private-flagged content removed.

    Sections marked [PRIVATE — DO NOT USE EXTERNALLY] or [INTERVIEW-ONLY ...]
    are stripped here, at the server boundary. The client never receives them.
    """
    if not PROFILE.exists():
        return "Master profile not found."

    kept, redacted, skipping = [], 0, False
    for line in PROFILE.read_text().splitlines():
        if any(marker in line for marker in PRIVATE_MARKERS):
            skipping = True
            redacted += 1
            kept.append("  [redacted: private content withheld by server]")
            continue
        # a private block ends at the next bullet or heading at column 0
        if skipping:
            if line.startswith(("- ", "#", "**")) or not line.strip():
                skipping = False
            else:
                continue
        kept.append(line)

    header = f"<!-- {redacted} private section(s) redacted at the server boundary -->\n"
    return header + "\n".join(kept)


# --------------------------------------------------------------------------

def _selftest() -> None:
    print("=== search_jobs('iot', min_score=10) ===")
    print(search_jobs("iot", 10, 3))
    print("=== get_pipeline() ===")
    print(get_pipeline()[:900])
    print("=== get_profile() redaction check ===")
    body = get_profile()
    leaked = [m for m in PRIVATE_MARKERS if m in body]
    print(f"length: {len(body)} chars")
    print(f"LEAKED private markers: {leaked or 'none — redaction working'}")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        _selftest()
    else:
        mcp.run()
