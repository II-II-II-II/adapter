# Recovering job descriptions from JS-only career sites

Many applicant-tracking systems render the posting client-side, so fetching
the page returns an empty shell or a browser-compatibility notice. The text is
usually available from an underlying endpoint.

**Why bother:** postings get taken down, and you want the exact wording when
you prepare for an interview three weeks later. Save a local copy of every JD
that matters (`source/jobs/`), and the `saved:` field in `jd_registry.yaml`
points at it.

---

## Greenhouse

Public and well-behaved. Board token is the slug in the public URL.

```bash
# All open roles, with full descriptions
curl -s "https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true"

# One role
curl -s "https://boards-api.greenhouse.io/v1/boards/<token>/jobs/<job_id>"
```

Note: `updated_at` is **not** a posted date. A req "updated" yesterday may be
months old.

## Lever

```bash
curl -s "https://api.lever.co/v0/postings/<company>?mode=json"
```

Returns an array with `text`, `categories` (location, team, commitment),
`createdAt` as an epoch in milliseconds, and `hostedUrl`. `createdAt` is a real
posted date, which makes Lever the most reliable source for "what's new."

## Ashby

```bash
curl -s "https://api.ashbyhq.com/posting-api/job-board/<company>"
```

## Workday

The public page is a JavaScript shell. The content sits behind the CXS endpoint.
Given a posting URL of the form
`https://<tenant>.wd5.myworkdayjobs.com/en-US/<site>/job/<City>/<Title>_<REQ>`:

```bash
curl -s -H "Accept: application/json" \
  "https://<tenant>.wd5.myworkdayjobs.com/wday/cxs/<tenant>/<site>/job/<City>/<Title>_<REQ>"
```

The `jobPostingInfo` object holds `title`, `jobDescription` as HTML,
`location`, `startDate` and `jobRequisitionId`. Note the host number varies by
tenant — `wd1`, `wd3`, `wd5` and others all occur; copy it from the browser URL.

## ADP WorkforceNow

Also a shell. The requisition API takes the `cid`, `ccId` and `jobId` straight
from the public URL's query string:

```bash
curl -s "https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions/<jobId>?cid=<cid>&ccId=<ccId>&lang=en_US"
```

`requisitionDescription` holds the posting body as HTML.
`requisitionLocations` holds the address. You can also drop the `jobId` path
segment to list **every** open requisition for that employer — useful for
finding a better-fitting role at the same company than the one you were sent.

---

## General technique when a site isn't listed here

1. Open the posting with browser dev tools on the Network tab, filtered to XHR.
2. Reload. The request returning the posting text is usually obvious by size.
3. Copy it as cURL, strip the headers back to `Accept: application/json` and a plain user agent, and confirm it still returns.

Most of these endpoints are public and unauthenticated because the job board
itself is public. Keep request volume low and sane — one posting at a time is
the use case here, not bulk harvesting.
