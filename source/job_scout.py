#!/usr/bin/env python3
"""
Job Scout — polls company ATS boards, filters against criteria, emits a shortlist.

    python3 source/job_scout.py                 # normal run
    python3 source/job_scout.py --verify        # only check which watchlist slugs resolve
    python3 source/job_scout.py --tag space     # limit to companies with a given tag
    python3 source/job_scout.py --no-dedupe     # ignore the seen-cache

Config:  source/job_filters.yaml
Roster:  source/company_watchlist.yaml
Output:  output/scout/shortlist_YYYY-MM-DD.md
"""
import argparse
import html
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "source" / "job_filters.yaml"
ROSTER = ROOT / "source" / "company_watchlist.yaml"
FRAMING = ROOT / "source" / "role_framing.yaml"
TIMEOUT = 20
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


# ---------------------------------------------------------------- utilities

def strip_html(s):
    if not s:
        return ""
    s = html.unescape(str(s))
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_date(v):
    """Best-effort date parse across ATS formats. Returns tz-aware UTC or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):  # epoch millis (Lever)
        try:
            return datetime.fromtimestamp(v / 1000, tz=timezone.utc)
        except (ValueError, OSError):
            return None
    s = str(v).strip().replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d", "%m/%d/%Y"):
        try:
            dt = datetime.fromisoformat(s) if fmt is None else datetime.strptime(s, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


SALARY_RE = re.compile(r"\$\s?(\d{2,3})[,\s]?(\d{3})(?:\.\d+)?(?:\s*[kK])?")


def extract_salaries(text):
    """Pull plausible annual salary figures out of free text."""
    vals = []
    for m in SALARY_RE.finditer(text or ""):
        try:
            v = int(m.group(1) + m.group(2))
        except ValueError:
            continue
        if 40_000 <= v <= 600_000:
            vals.append(v)
    return (min(vals), max(vals)) if vals else (None, None)


YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:or more\s*)?years?", re.I)


def extract_min_years(text):
    """Smallest 'N years' requirement mentioned — proxy for seniority floor."""
    hits = [int(m.group(1)) for m in YEARS_RE.finditer(text or "")]
    hits = [h for h in hits if 0 < h <= 30]
    return min(hits) if hits else None


# ---------------------------------------------------------------- adapters
# Each returns a list of normalized dicts.

def norm(company, tags, title, location, url, posted, desc, smin=None, smax=None):
    return {
        "company": company, "tags": tags, "title": title or "",
        "location": location or "", "url": url or "",
        "posted": posted, "description": desc or "",
        "salary_min": smin, "salary_max": smax,
    }


def fetch_greenhouse(c):
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{c['slug']}/jobs",
        params={"content": "true"}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        out.append(norm(
            c["name"], c.get("tags", []), j.get("title"),
            (j.get("location") or {}).get("name"),
            j.get("absolute_url"), parse_date(j.get("updated_at")),
            strip_html(j.get("content"))))
    return out


def fetch_lever(c):
    r = requests.get(f"https://api.lever.co/v0/postings/{c['slug']}",
                     params={"mode": "json"}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict):
        raise ValueError(data.get("error", "unexpected response"))
    out = []
    for j in data:
        cats = j.get("categories") or {}
        loc = cats.get("location") or ""
        if j.get("workplaceType"):
            loc = f"{loc} ({j['workplaceType']})"
        out.append(norm(
            c["name"], c.get("tags", []), j.get("text"), loc,
            j.get("hostedUrl"), parse_date(j.get("createdAt")),
            j.get("descriptionPlain") or strip_html(j.get("description"))))
    return out


def fetch_ashby(c):
    r = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{c['slug']}",
        params={"includeCompensation": "true"}, headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        loc = j.get("location") or ""
        wt = (j.get("workplaceType") or "").strip()
        if wt:
            loc = f"{loc} ({wt})"
        # Only treat as remote when Ashby actually says Remote — isRemote is true
        # for hybrid postings too, which produced false positives.
        if j.get("isRemote") and wt.lower() == "remote":
            loc += " remote"
        out.append(norm(
            c["name"], c.get("tags", []), j.get("title"), loc,
            j.get("jobUrl"), parse_date(j.get("publishedAt")),
            strip_html(j.get("descriptionHtml"))))
    return out


def fetch_bamboohr(c):
    r = requests.get(f"https://{c['slug']}.bamboohr.com/careers/list",
                     headers={**UA, "Accept": "application/json"}, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for j in (r.json().get("result") or []):
        loc = j.get("location") or {}
        loc_s = " ".join(filter(None, [loc.get("city"), loc.get("state")]))
        if str(j.get("isRemote", "")).lower() in ("true", "1", "yes"):
            loc_s += " remote"
        out.append(norm(
            c["name"], c.get("tags", []), j.get("jobOpeningName"), loc_s,
            f"https://{c['slug']}.bamboohr.com/careers/{j.get('id')}",
            parse_date(j.get("datePosted")), ""))
    return out


ADAPTERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever,
            "ashby": fetch_ashby, "bamboohr": fetch_bamboohr}


# ---------------------------------------------------------------- BuiltIn
# The watchlist gives depth (every opening at companies we chose). BuiltIn gives
# breadth (companies that will never be on any list we build). Search terms live
# in job_filters.yaml -> builtin.searches, so they're editable without code changes.
# robots.txt disallows /admin/, /user/, /search/ — not /jobs/ or /job/ (checked
# 2026-08-12). Listing cards carry title, age, location, salary and level, so no
# per-job detail fetch is needed to filter.

BI_CARD = re.compile(
    r'<h2[^>]*>\s*<a[^>]*href="(?P<url>/job/[^"]+)"[^>]*>(?P<title>[^<]{4,120})</a>',
    re.I)
BI_AGE = re.compile(r"(\d+)\s+(Day|Hour|Minute)s?\s+Ago", re.I)
BI_SAL = re.compile(r"(\d{2,3})K-(\d{2,3})K\s+Annually", re.I)
BI_LOC = re.compile(r"([A-Z][A-Za-z .'\-]+,\s*[A-Z]{2},\s*USA)")
BI_CO_ALT = re.compile(r'alt="([^"]{2,60}?)\s+Logo"', re.I)
BI_CO_HREF = re.compile(r'href="/company/([a-z0-9\-]{2,60})"', re.I)


def fetch_jobicy(cfg):
    """Jobicy — remote-job API. Breadth source #2, added 2026-09-04.

    Strictly better shaped than the BuiltIn scrape: it returns the real posted
    date, structured salaryMin/salaryMax, and the FULL job description. So the
    freshness filter, the salary floor and jd_flag all work on the first pass —
    no enrichment fetch, no HTML regex, no throttling delay.

    Chosen on evidence: against Ian's converting title patterns it returned 7
    matches per 100 postings (incl. a Forward Deployed Engineer req), where The
    Muse returned 0/60, RemoteOK 1/100 and Remotive 1/18.
    """
    jc = cfg.get("jobicy") or {}
    if not jc.get("enabled", True):
        return []
    geo = jc.get("geo", "usa")
    count = jc.get("count", 200)
    out, seen = [], set()
    # A bare pull plus optional tag searches; the tag param narrows server-side.
    queries = [{"count": count, "geo": geo}]
    for t in jc.get("tags", []):
        queries.append({"count": 100, "geo": geo, "tag": t})
    for q in queries:
        try:
            r = requests.get("https://jobicy.com/api/v2/remote-jobs",
                             params=q, headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            jobs = r.json().get("jobs", [])
        except Exception:  # noqa: BLE001 — one bad query must not kill the pass
            continue
        for j in jobs:
            url = j.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            geo_s = j.get("jobGeo") or ""
            # Everything here is a remote board; make that explicit so the
            # location filter's remote_patterns match instead of rejecting.
            loc = f"{geo_s} remote" if "remote" not in geo_s.lower() else geo_s
            smin, smax = j.get("salaryMin"), j.get("salaryMax")
            if str(j.get("salaryPeriod", "yearly")).lower() != "yearly":
                smin = smax = None
            out.append(norm(
                j.get("companyName") or "Jobicy listing", ["jobicy"],
                j.get("jobTitle"), loc, url, parse_date(j.get("pubDate")),
                strip_html(j.get("jobDescription")),
                smin if isinstance(smin, int) else None,
                smax if isinstance(smax, int) else None))
    return out


def enrich_builtin(jobs, cfg):
    """Fetch real JD bodies for surfaced BuiltIn jobs and re-run the flag check.

    `fetch_builtin` can only see the search-results *card* — company, location,
    salary, age — so the text it stores as a description is listing chrome, not
    the posting. `jd_flag` therefore never fired on BuiltIn results, and three of
    five hand-picked roles on 2026-09-03 died on requirements the flags already
    covered ("Kubernetes-based platform", "strong full-stack development").

    Runs AFTER scoring and capping, so it costs one request per surfaced job
    (~25) rather than one per posting scanned (~650).
    """
    fr = cfg.get("_framing") or {}
    pats = fr.get("jd_flag", {}).get("patterns", [])
    if not pats:
        return
    targets = [j for j in jobs if "builtin" in j.get("tags", [])]
    if not targets:
        return

    def pull(j):
        # Short timeout and no retry: a slow board must not blow the scan's
        # overall budget. Sequential fetching pushed a run past 180s once.
        try:
            r = requests.get(j["url"], headers=UA, timeout=8)
            return j, (strip_html(r.text)[:20000] if r.status_code == 200 else None)
        except Exception:  # noqa: BLE001 — enrichment is best-effort, never fatal
            return j, None

    with ThreadPoolExecutor(max_workers=8) as pool:
        for j, body in pool.map(pull, targets):
            if not body:
                continue
            j["description"] = body
            if matches_any(f"{j['title']} {body}".lower(), pats):
                j["jd_flag"] = "JD demands software-engineering years / hard credential"


def fetch_builtin(cfg):
    """Search BuiltIn for target titles. Returns normalized job dicts."""
    bi = cfg.get("builtin") or {}
    if not bi.get("enabled", True):
        return []
    out, seen_urls = [], set()
    # Be a good citizen and stay reliable: 23 back-to-back searches got throttled
    # (433 postings on one run, 177 on the next). A short pause fixes both.
    delay = bi.get("delay_seconds", 2)
    for i, term in enumerate(bi.get("searches", [])):
        if i:
            time.sleep(delay)
        path = bi.get("path", "/jobs/remote")
        url = f"https://builtin.com{path}"
        try:
            r = requests.get(url, params={"search": term}, headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            page = r.text
        except Exception:  # noqa: BLE001 - one bad search shouldn't kill the run
            continue
        for m in BI_CARD.finditer(page):
            full = "https://builtin.com" + m.group("url")
            if full in seen_urls:
                continue
            seen_urls.add(full)
            # Company sits above the title as alt="<Name> Logo" / /company/<slug>.
            # Without it every posting shares one name and max_per_company caps
            # the entire BuiltIn pass at 3 results.
            pre = page[max(0, m.start() - 2500):m.start()]
            cm = BI_CO_ALT.findall(pre) or BI_CO_HREF.findall(pre)
            company = (html.unescape(cm[-1]).replace("-", " ").title().strip()
                       if cm else "BuiltIn listing")
            tail = re.sub(r"<[^>]+>", " | ", page[m.end():m.end() + 2000])
            tail = html.unescape(re.sub(r"(\s*\|\s*)+", " | ", tail))
            age = BI_AGE.search(tail)
            posted = None
            if age:
                n, unit = int(age.group(1)), age.group(2).lower()
                days = n if unit == "day" else 0
                posted = datetime.now(timezone.utc) - timedelta(days=days)
            sal = BI_SAL.search(tail)
            smin = int(sal.group(1)) * 1000 if sal else None
            smax = int(sal.group(2)) * 1000 if sal else None
            locm = BI_LOC.search(tail)
            loc = locm.group(1) if locm else ""
            if re.search(r"\bRemote\b", tail[:200], re.I):
                loc = f"Remote — {loc}" if loc else "Remote"
            out.append(norm(company, ["builtin"],
                            html.unescape(m.group("title")).strip(),
                            loc, full, posted, tail[:1200], smin, smax))
    return out


# ---------------------------------------------------------------- filtering

def _word_re(p):
    """Compile a pattern to match on word boundaries, not as a substring.

    Plain `p in text` matched "ote" (on-target-earnings) inside "remote" and
    "potential", so every remote posting flagged. Boundaries are added only where
    the pattern actually starts/ends with a word character — appending \\b after
    "u.s." or "node.js" would never match, since \\b needs a word char adjacent.
    """
    r = re.escape(p)
    if p[:1].isalnum():
        r = r"\b" + r
    if p[-1:].isalnum():
        r = r + r"\b"
    return re.compile(r)


_WORD_RE_CACHE = {}


def matches_any(text, patterns):
    t = (text or "").lower()
    for p in patterns:
        p = p.lower()
        if p.endswith("$"):
            if re.search(p[:-1] + r"\s*$", t):
                return True
        else:
            rx = _WORD_RE_CACHE.get(p)
            if rx is None:
                rx = _WORD_RE_CACHE[p] = _word_re(p)
            if rx.search(t):
                return True
    return False


def evaluate(job, cfg):
    """Return (verdict, reason, score). verdict in {'drop','keep'}."""
    f_loc, f_lvl, f_kw = cfg["location"], cfg["level"], cfg["keywords"]
    title, loc = job["title"], job["location"]
    blob = f"{title} {job['description']}".lower()

    if matches_any(job["company"], cfg.get("excluded_companies", [])):
        return "drop", "excluded company", 0

    # --- cheap: title
    if matches_any(title, f_lvl.get("reject_title_patterns", [])):
        return "drop", "junior-coded title", 0

    # --- cheap: freshness
    max_age = cfg["freshness"]["max_age_days"]
    if job["posted"]:
        age = (datetime.now(timezone.utc) - job["posted"]).days
        if age > max_age:
            return "drop", f"stale ({age}d)", 0
        job["age_days"] = age

    # --- cheap: location
    if f_loc.get("remote_required", True):
        if matches_any(loc, f_loc.get("reject_patterns", [])):
            return "drop", f"location excluded ({loc})", 0
        explicit = matches_any(loc, f_loc.get("remote_patterns", []))
        local = matches_any(loc, f_loc.get("also_accept_local", []))
        ambiguous = False
        if not explicit and not local:
            # Country-level-only strings ("United States") are plausibly remote.
            # But "San Mateo, CA United States" names a city -> treat as onsite.
            residue = (loc or "").lower()
            for p in f_loc.get("ambiguous_patterns", []):
                residue = residue.replace(p.lower(), " ")
            residue = re.sub(r"[^a-z]+", "", residue)
            if residue:
                return "drop", f"not remote ({loc})", 0
            ambiguous = True
        job["local_match"] = local and not explicit
        job["verify_remote"] = ambiguous

    # --- deep: disqualifying language
    if matches_any(blob, f_kw.get("disqualifying", [])):
        return "drop", "disqualifying requirement", 0

    # --- deep: salary
    # Don't clobber salary an adapter already parsed. BuiltIn cards render
    # "130K-160K Annually" — no dollar sign, no comma-thousands — so SALARY_RE
    # finds nothing and would wipe a perfectly good figure back to None.
    smin, smax = extract_salaries(job["description"])
    if smin is None and job.get("salary_min") is not None:
        smin, smax = job["salary_min"], job["salary_max"]
    job["salary_min"], job["salary_max"] = smin, smax
    floor = f_lvl.get("min_salary_max")
    if smax and floor and smax < floor:
        return "drop", f"salary max ${smax:,} below floor", 0

    # --- deep: seniority floor
    yrs = extract_min_years(job["description"])
    job["min_years"] = yrs
    if yrs is not None and yrs < f_lvl.get("min_years_required", 0):
        return "drop", f"junior-coded ({yrs}y minimum)", 0
    if yrs is not None and yrs > f_lvl.get("max_years_required", 99):
        job["flag"] = f"demands {yrs}+ years"

    # --- score (word-boundary matching: "rag" must not hit inside "storage",
    #     "sso" must not hit inside "associate")
    def kw_hit(kw, text):
        return re.search(r"(?<![a-z0-9])" + re.escape(kw.lower()) + r"(?![a-z0-9])", text)

    score = 0
    hits = []
    for k in f_kw.get("strong", []):
        if kw_hit(k, blob):
            score += 3
            hits.append(k)
    for k in f_kw.get("good", []):
        if kw_hit(k, blob):
            score += 1
            hits.append(k)
    # --- role framing (source/role_framing.yaml — edit that file, not this code)
    #     The TITLE carries the signal, not the JD body. A posting can demand
    #     "7+ years of software engineering experience" and still be a strong
    #     fit, if its title is something like "Senior Forward Deployed Engineer."
    #     JD phrases annotate; titles decide.
    fr = cfg.get("_framing") or {}
    tl = (title or "").lower()
    boost = fr.get("title_boost", {})
    if matches_any(tl, boost.get("patterns", [])):
        score += boost.get("weight", 0)
        hits.append("↑framing")
    pen = fr.get("title_penalty", {})
    if matches_any(tl, pen.get("patterns", [])):
        score += pen.get("weight", 0)
        hits.append("↓framing")
    if matches_any(blob, fr.get("jd_flag", {}).get("patterns", [])):
        job["jd_flag"] = "JD demands software-engineering years / hard credential"

    job["hits"] = hits
    job["score"] = score

    if score < cfg["scoring"]["min_score_to_surface"]:
        return "drop", f"low score ({score})", score
    return "keep", "", score


# ---------------------------------------------------------------- dedupe

def load_seen(path):
    try:
        return set(json.loads(Path(path).read_text()))
    except (OSError, ValueError):
        return set()


def known_companies(md_path):
    try:
        txt = Path(md_path).read_text().lower()
    except OSError:
        return set()
    return {n for n in re.findall(r"\*\*([A-Za-z0-9 .&'\-]+)\*\*", txt)}


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="only test slug resolution")
    ap.add_argument("--tag", help="limit to companies with this tag")
    ap.add_argument("--no-dedupe", action="store_true")
    ap.add_argument("--no-builtin", action="store_true",
                    help="skip the BuiltIn breadth pass (watchlist only)")
    ap.add_argument("--no-jobicy", action="store_true",
                    help="skip the Jobicy breadth pass")
    args = ap.parse_args()

    cfg = yaml.safe_load(CFG.read_text())
    try:
        cfg["_framing"] = yaml.safe_load(FRAMING.read_text())
    except OSError:
        cfg["_framing"] = {}
        print("  note: source/role_framing.yaml not found — framing scoring disabled")
    roster = yaml.safe_load(ROSTER.read_text())
    if args.tag:
        roster = [c for c in roster if args.tag in (c.get("tags") or [])]

    seen_path = ROOT / cfg["output"]["seen_cache"]
    seen = set() if args.no_dedupe else load_seen(seen_path)

    kept, dropped, failures, total = [], {}, [], 0

    for c in roster:
        fn = ADAPTERS.get(c["ats"])
        if not fn:
            failures.append((c["name"], f"no adapter for {c['ats']}"))
            continue
        try:
            jobs = fn(c)
        except Exception as e:  # noqa: BLE001 - report and continue
            failures.append((c["name"], f"{type(e).__name__}: {str(e)[:80]}"))
            continue
        if args.verify:
            print(f"  OK   {c['name']:28s} {len(jobs):4d} jobs")
            continue
        total += len(jobs)
        for j in jobs:
            verdict, reason, _ = evaluate(j, cfg)
            if verdict == "drop":
                dropped[reason.split(" (")[0]] = dropped.get(reason.split(" (")[0], 0) + 1
                continue
            if j["url"] in seen:
                dropped["already seen"] = dropped.get("already seen", 0) + 1
                continue
            kept.append(j)

    # BuiltIn — breadth pass, searched by role framing rather than by skill.
    if not args.verify and not args.tag and not args.no_builtin:
        try:
            bi_jobs = fetch_builtin(cfg)
            total += len(bi_jobs)
            print(f"  BuiltIn: {len(bi_jobs)} postings across "
                  f"{len((cfg.get('builtin') or {}).get('searches', []))} searches")
            for j in bi_jobs:
                verdict, reason, _ = evaluate(j, cfg)
                if verdict == "drop":
                    k = reason.split(" (")[0]
                    dropped[k] = dropped.get(k, 0) + 1
                    continue
                if j["url"] in seen:
                    dropped["already seen"] = dropped.get("already seen", 0) + 1
                    continue
                kept.append(j)
        except Exception as e:  # noqa: BLE001
            failures.append(("BuiltIn", f"{type(e).__name__}: {str(e)[:80]}"))

    # Jobicy — breadth source #2. Real dates, structured salary, full JD text,
    # so it needs no enrichment pass and the flags work immediately.
    if not args.verify and not args.tag and not args.no_jobicy:
        try:
            jy_jobs = fetch_jobicy(cfg)
            total += len(jy_jobs)
            print(f"  Jobicy: {len(jy_jobs)} postings")
            for j in jy_jobs:
                verdict, reason, _ = evaluate(j, cfg)
                if verdict == "drop":
                    dropped[reason.split(" (")[0]] = \
                        dropped.get(reason.split(" (")[0], 0) + 1
                    continue
                if j["url"] in seen:
                    dropped["already seen"] = dropped.get("already seen", 0) + 1
                    continue
                kept.append(j)
        except Exception as e:  # noqa: BLE001
            failures.append(("Jobicy", f"{type(e).__name__}: {str(e)[:80]}"))

    if args.verify:
        print("\nFailures:")
        for n, e in failures:
            print(f"  FAIL {n:28s} {e}")
        return

    kept.sort(key=lambda j: (-j["score"], j.get("age_days", 99)))

    # Cap per company so one big board can't flood the shortlist.
    per_cap = cfg["scoring"].get("max_per_company", 3)
    capped, counts = [], {}
    for j in kept:
        n = counts.get(j["company"], 0)
        if n >= per_cap:
            dropped["over per-company cap"] = dropped.get("over per-company cap", 0) + 1
            continue
        counts[j["company"]] = n + 1
        capped.append(j)
    kept = capped[: cfg["scoring"]["max_results_per_run"]]

    # BuiltIn cards carry no JD body, so jd_flag can only work once the real
    # posting is fetched. Done here — after the cap — so it's ~25 requests.
    if not args.no_builtin:
        try:
            enrich_builtin(kept, cfg)
        except Exception as e:  # noqa: BLE001
            failures.append(("BuiltIn enrich", f"{type(e).__name__}: {str(e)[:80]}"))

    today = datetime.now().strftime("%Y-%m-%d")
    outdir = ROOT / cfg["output"]["directory"]
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"shortlist_{today}.md"

    lines = [f"# Job Scout — {today}", ""]
    lines.append(f"Scanned **{total}** postings across **{len(roster)}** companies → "
                 f"**{len(kept)}** surfaced.")
    lines.append("")
    if kept:
        for j in kept:
            sal = ""
            if j.get("salary_max"):
                sal = f" · ${j['salary_min']:,}–${j['salary_max']:,}" if j.get("salary_min") \
                    else f" · up to ${j['salary_max']:,}"
            age = f" · {j['age_days']}d old" if j.get("age_days") is not None else ""
            yrs = f" · {j['min_years']}+ yrs" if j.get("min_years") else ""
            lines.append(f"### [{j['score']}] {j['company']} — {j['title']}")
            lines.append(f"{j['location']}{sal}{age}{yrs}")
            if j.get("flag"):
                lines.append(f"> ⚠ {j['flag']}")
            # Was never rendered: the check writes `jd_flag`, the writer only read
            # `flag`, so every screen-warning computed since this was added was
            # silently discarded. Found 2026-09-04.
            if j.get("jd_flag"):
                lines.append(f"> ⚠ {j['jd_flag']}")
            if j.get("local_match"):
                lines.append("> 📍 local (not remote) — matched home-metro exception")
            if j.get("verify_remote"):
                lines.append("> ❓ location is country-level only — verify it's actually remote")
            lines.append(f"Matched: {', '.join(j['hits'][:10])}")
            lines.append(f"{j['url']}")
            lines.append("")
    else:
        lines.append("_Nothing cleared the filters this run._\n")

    lines.append("## Filtered out")
    for reason, n in sorted(dropped.items(), key=lambda x: -x[1]):
        lines.append(f"- {reason}: {n}")
    if failures:
        lines.append("\n## Boards that failed (fix or drop these slugs)")
        for n, e in failures:
            lines.append(f"- **{n}** — {e}")

    out.write_text("\n".join(lines) + "\n")

    if not args.no_dedupe:
        seen.update(j["url"] for j in kept)
        seen_path.write_text(json.dumps(sorted(seen)))

    print(f"Scanned {total} postings / {len(roster)} companies → {len(kept)} surfaced")
    print(f"Wrote {out}")
    if failures:
        print(f"{len(failures)} board(s) failed — see the report")


if __name__ == "__main__":
    sys.exit(main())
