"""
Shared Google OAuth handling for the read-only MCP tools (Gmail, Calendar).

One credential, one token cache, scoped to the narrowest set of read-only
permissions the connected APIs need. Google enforces that boundary at the
token level — this code can't exceed it even if a bug tried to.
"""
from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent
CREDENTIALS_FILE = ROOT / "gmail_credentials.json"  # same OAuth client, kept at its existing path
TOKEN_FILE = ROOT / "google_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_credentials() -> Credentials:
    """Load a cached token, refresh it silently if expired, or run the
    one-time browser consent flow (covering every scope above) if no
    valid token exists yet."""
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except Exception:
                # Google expires refresh tokens after 7 days while the OAuth app
                # is still in "Testing" publishing status. Don't crash — drop the
                # dead token and fall through to a fresh consent flow.
                TOKEN_FILE.unlink(missing_ok=True)
                creds = None
        if not refreshed:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"{CREDENTIALS_FILE} not found — download the OAuth "
                    "client JSON from Google Cloud Console first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


if __name__ == "__main__":
    # One-time (or re-run-after-adding-a-scope) setup: completes the
    # browser consent flow for every scope above and caches a token.
    get_credentials()
    print(f"Token cached at {TOKEN_FILE}. Auth complete.")
