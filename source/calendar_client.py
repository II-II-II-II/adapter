"""
Google Calendar read-only client.

Scope is calendar.readonly — can list/read events, cannot create, edit,
or delete anything on the calendar. Same shared credential as Gmail
(see google_auth.py), same "read-only enforced by Google, not by this
code" boundary.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build

from google_auth import get_credentials


def _meeting_link(event):
    """Find a join URL. Google Meet exposes hangoutLink, but Zoom/Teams
    invites put it in conferenceData.entryPoints — missing that is how a
    real invite looks linkless."""
    if event.get("hangoutLink"):
        return event["hangoutLink"]
    conference = event.get("conferenceData") or {}
    for entry in conference.get("entryPoints", []):
        if entry.get("entryPointType") == "video" and entry.get("uri"):
            return entry["uri"]
    return ""


def _clean_description(raw):
    """Invite bodies are usually HTML. Strip tags to readable text."""
    if not raw:
        return ""
    text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", raw)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def fetch_upcoming_events(days_ahead: int = 14, max_results: int = 20) -> list[dict]:
    """Events on the primary calendar between now and `days_ahead` days out."""
    creds = get_credentials()
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    resp = service.events().list(
        calendarId="primary",
        timeMin=time_min,
        timeMax=time_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    results = []
    for ev in resp.get("items", []):
        start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
        end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date", "")
        attendees = [a.get("email", "") for a in ev.get("attendees", [])]
        results.append({
            "id": ev.get("id", ""),
            "summary": ev.get("summary", "(no title)"),
            "start": start,
            "end": end,
            "location": ev.get("location", ""),
            "attendees": attendees,
            "meeting_link": _meeting_link(ev),
            "description": _clean_description(ev.get("description"))[:1200],
        })
    return results
