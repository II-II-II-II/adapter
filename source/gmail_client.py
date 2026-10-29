"""
Gmail read-only client.

Scope is the narrowest Google offers for reading mail: gmail.readonly.
This credential cannot send, delete, or modify anything — Google enforces
that at the token level, not in this code.

Only headers + snippet are ever fetched by default (format="metadata").
Full message bodies are only pulled on demand, one message at a time,
via fetch_message_body.
"""
from __future__ import annotations

import base64
import re

from googleapiclient.discovery import build

from google_auth import get_credentials

MAX_BODY_CHARS = 6000


def fetch_recent_messages(days: int = 30, max_results: int = 25,
                          query: str = "") -> list[dict]:
    """Headers + snippet for recent messages. No bodies.

    `query` accepts raw Gmail search syntax and is ANDed with the date window —
    e.g. "from:recruiter@co.com", "subject:interview", "has:attachment".
    Without it, scanning for one company means pulling hundreds of unrelated
    messages and filtering by eye, which is slow and burns context.

    Drafts are labeled explicitly. Gmail returns them alongside sent mail with
    an identical shape, and reading an autosave timestamp as a send once caused
    a real error here.
    """
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    q = f"newer_than:{days}d"
    if query:
        q = f"{q} {query}"

    resp = service.users().messages().list(
        userId="me", q=q, maxResults=max_results
    ).execute()

    results = []
    for ref in resp.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=ref["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        labels = msg.get("labelIds", [])
        results.append({
            "id": ref["id"],
            "from": headers.get("From", "(unknown)"),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
            "is_draft": "DRAFT" in labels,
            "is_sent": "SENT" in labels,
        })
    return results


def _decode_body_data(data: str) -> str:
    """Gmail base64url-encodes body parts; decode to text."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_plain_text(payload: dict) -> str:
    """Walk a message payload for the best available text. Prefers
    text/plain; falls back to a crude tag-strip of text/html if that's
    all the message has."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_body_data(payload["body"]["data"])

    for part in payload.get("parts", []) or []:
        text = _extract_plain_text(part)
        if text:
            return text

    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        html = _decode_body_data(payload["body"]["data"])
        return re.sub(r"<[^>]+>", " ", html)

    return ""


def fetch_message_body(message_id: str) -> dict:
    """Full content of one specific message — headers plus the actual
    body text, fetched on demand. Only called for a message you've
    already seen and specifically chosen to read further."""
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    body = _extract_plain_text(msg["payload"]).strip() or "(no readable text body found)"
    truncated = False
    if len(body) > MAX_BODY_CHARS:
        body = body[:MAX_BODY_CHARS]
        truncated = True

    return {
        "from": headers.get("From", "(unknown)"),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", "(no subject)"),
        "date": headers.get("Date", ""),
        "body": body,
        "truncated": truncated,
    }
