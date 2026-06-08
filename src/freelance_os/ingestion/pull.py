"""Public API fetchers + normalizer for freelance-os pull command."""

import json
import logging
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_lead(source: str, url: str, title: str, description: str) -> Dict[str, Any]:
    return {
        "source": source,
        "url": url,
        "title": title,
        "description": description,
        "budget": {"amount": None, "currency": "USD", "type": "unknown"},
        "skills": [],
        "posted_at": None,
        "client": {},
        "location": None,
        "remote": True,
    }


# Several public APIs (Remotive, Jobicy) 403 the bare `Python-urllib` UA as a
# bot, so every request sends a descriptive identifier by default.
_DEFAULT_UA = (
    "freelance-revenue-os/0.1 (public API research client; "
    "github.com/freelance-revenue-os)"
)


def _fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Any:
    """Fetch JSON from a URL. Raises on network/HTTP errors."""
    hdrs = {"User-Agent": _DEFAULT_UA}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_salary_string(salary: str) -> Dict[str, Any]:
    """Parse a salary string like '$50k-100k' or '$50/hr' into a budget dict."""
    import re

    salary = salary.strip()
    if not salary:
        return {"amount": None, "currency": "USD", "type": "unknown"}

    currency = "USD"
    if "EUR" in salary or "€" in salary:
        currency = "EUR"
    elif "GBP" in salary or "£" in salary:
        currency = "GBP"
    elif "CAD" in salary:
        currency = "CAD"
    elif "AUD" in salary:
        currency = "AUD"

    s_lower = salary.lower()
    _HOURLY_CUES = ["/hr", "/hour", "hourly", "per hour", "/h"]
    _ANNUAL_CUES = ["/year", "/yr", "year", "yr", "annual", "annually", "salary", "per annum"]
    _FIXED_CUES = ["fixed price", "project budget", "one-time", "contract value"]

    budget_type = "fixed"
    if any(x in s_lower for x in _HOURLY_CUES):
        budget_type = "hourly"
    elif any(x in s_lower for x in _FIXED_CUES):
        budget_type = "fixed"
    elif any(x in s_lower for x in _ANNUAL_CUES):
        budget_type = "annual"

    numbers = re.findall(r"[\d,]+(?:\.\d+)?[kK]?", salary)
    amounts = []
    for n in numbers:
        n_clean = n.replace(",", "")
        if n_clean.endswith(("k", "K")):
            n_clean = n_clean[:-1] + "000"
        try:
            amounts.append(float(n_clean))
        except ValueError:
            pass

    if not amounts:
        return {"amount": None, "currency": currency, "type": budget_type}

    amount = sum(amounts) / len(amounts)
    return {"amount": amount, "currency": currency, "type": budget_type}


def _parse_iso(date_str: Optional[str]) -> Optional[str]:
    """Parse an ISO-ish date string, return normalized ISO 8601 or None."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Remotive
# ---------------------------------------------------------------------------

def fetch_remotive() -> List[Dict[str, Any]]:
    """Fetch jobs from the Remotive public API."""
    try:
        data = _fetch_json("https://remotive.com/api/remote-jobs")
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        results = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            lead = _empty_lead(
                source="remotive",
                url=job.get("url", ""),
                title=job.get("title", ""),
                description=job.get("description", "") or "",
            )
            lead["budget"] = _parse_salary_string(job.get("salary", "") or "")
            lead["skills"] = job.get("tags", []) or []
            lead["posted_at"] = _parse_iso(job.get("publication_date"))
            lead["location"] = job.get("candidate_required_location", "") or ""
            results.append(lead)
        return results
    except Exception as exc:
        logger.warning("remotive fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# RemoteOK
# ---------------------------------------------------------------------------

_REMOTEOK_UA = (
    "freelance-revenue-os/0.1 (public API research client; "
    "github.com/freelance-revenue-os)"
)


def fetch_remoteok() -> List[Dict[str, Any]]:
    """Fetch jobs from RemoteOK. Skips the first element (metadata notice)."""
    try:
        data = _fetch_json(
            "https://remoteok.com/api",
            headers={"User-Agent": _REMOTEOK_UA},
        )
        if not isinstance(data, list):
            return []
        data = data[1:]  # first element is a metadata/legal notice
        results = []
        for job in data:
            if not isinstance(job, dict):
                continue
            job_id = job.get("id", "")
            url = job.get("url", "") or f"https://remoteok.com/remote-jobs/{job_id}"
            lead = _empty_lead(
                source="remoteok",
                url=url,
                title=job.get("position", "") or job.get("title", ""),
                description=job.get("description", "") or "",
            )
            sal_min = job.get("salary_min")
            sal_max = job.get("salary_max")
            if sal_min is not None or sal_max is not None:
                vals = [v for v in [sal_min, sal_max] if v is not None]
                lead["budget"] = {
                    "amount": sum(vals) / len(vals),
                    "currency": "USD",
                    "type": "annual",
                }
            tags = job.get("tags", [])
            lead["skills"] = tags if isinstance(tags, list) else []
            lead["posted_at"] = _parse_iso(job.get("date"))
            results.append(lead)
        return results
    except Exception as exc:
        logger.warning("remoteok fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Jobicy
# ---------------------------------------------------------------------------

def fetch_jobicy() -> List[Dict[str, Any]]:
    """Fetch jobs from Jobicy API."""
    try:
        data = _fetch_json("https://jobicy.com/api/v2/remote-jobs")
        jobs = data.get("jobs", []) if isinstance(data, dict) else []
        results = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            lead = _empty_lead(
                source="jobicy",
                url=job.get("url", "") or job.get("jobGeo", ""),
                title=job.get("jobTitle", "") or job.get("title", ""),
                description=job.get("jobDescription", "") or job.get("description", ""),
            )
            sal_min = job.get("annualSalaryMin") or job.get("salaryMin")
            sal_max = job.get("annualSalaryMax") or job.get("salaryMax")
            if sal_min is not None or sal_max is not None:
                vals = [v for v in [sal_min, sal_max] if v is not None]
                lead["budget"] = {
                    "amount": sum(vals) / len(vals),
                    "currency": "USD",
                    "type": "annual",
                }
            skills = job.get("jobIndustry", []) or job.get("tags", [])
            lead["skills"] = skills if isinstance(skills, list) else []
            lead["posted_at"] = _parse_iso(job.get("pubDate") or job.get("publishedAt"))
            lead["location"] = job.get("jobGeo", "") or ""
            results.append(lead)
        return results
    except Exception as exc:
        logger.warning("jobicy fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Hacker News (Algolia) — "Ask HN: Freelancer? Seeking freelancer?" thread
# ---------------------------------------------------------------------------

def _find_hn_thread_id() -> Optional[str]:
    """Find the current month's 'Ask HN: Freelancer?' story ID via Algolia."""
    year = date.today().year
    query = urllib.parse.quote(f"Ask HN Freelancer Seeking freelancer {year}")
    url = (
        f"https://hn.algolia.com/api/v1/search"
        f"?query={query}&tags=story&hitsPerPage=10"
    )
    try:
        data = _fetch_json(url)
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            if "Freelancer?" in title and "Seeking" in title:
                return str(hit.get("objectID") or hit.get("story_id", ""))
    except Exception as exc:
        logger.warning("HN thread search failed: %s", exc)
    return None


def fetch_hn_freelancer() -> List[Dict[str, Any]]:
    """Fetch 'seeking freelancer' comments from the HN monthly thread."""
    try:
        thread_id = _find_hn_thread_id()
        if not thread_id:
            logger.warning("HN: could not find freelancer thread; skipping")
            return []
        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?tags=comment,story_{thread_id}&hitsPerPage=100"
        )
        data = _fetch_json(url)
        results = []
        for hit in data.get("hits", []):
            text = hit.get("comment_text", "") or ""
            if len(text) < 20:
                continue
            text_lower = text.lower()
            # Include only "seeking freelancer" / hiring comments (not "AVAILABLE" posts)
            _seeking_phrases = [
                "seeking freelancer", "we are hiring", "we're hiring",
                "looking for a freelancer", "looking for a developer", "looking for a dev",
                "need a developer", "need a freelancer", "need a programmer",
            ]
            if not any(kw in text_lower for kw in _seeking_phrases):
                continue
            object_id = hit.get("objectID", "")
            hn_url = f"https://news.ycombinator.com/item?id={object_id}"
            first_line = text.split("\n")[0][:120].strip()
            lead = _empty_lead(
                source="hn_freelancer",
                url=hn_url,
                title=first_line or "HN Freelancer Thread",
                description=text[:2000],
            )
            lead["posted_at"] = _parse_iso(hit.get("created_at"))
            results.append(lead)
        return results
    except Exception as exc:
        logger.warning("HN freelancer fetch failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Dedupe + dispatch
# ---------------------------------------------------------------------------

def dedupe_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by URL; leads with no URL are kept."""
    seen: set = set()
    result = []
    for lead in leads:
        url = lead.get("url") or ""
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        result.append(lead)
    return result


SOURCES: Dict[str, Any] = {
    "remotive": fetch_remotive,
    "remoteok": fetch_remoteok,
    "jobicy": fetch_jobicy,
    "hn": fetch_hn_freelancer,
}


def fetch_leads(sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Fetch + deduplicate leads from all (or named) sources."""
    requested = sources or list(SOURCES.keys())
    all_leads: List[Dict[str, Any]] = []
    for name in requested:
        fetcher = SOURCES.get(name)
        if fetcher is None:
            logger.warning("unknown source: %s", name)
            continue
        leads = fetcher()
        all_leads.extend(leads)
    return dedupe_leads(all_leads)
