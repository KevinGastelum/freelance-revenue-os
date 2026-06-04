"""Read-only IMAP fetcher for job-alert emails.

Credentials come ONLY from environment variables — never hardcoded, logged,
or committed. Performs READ-ONLY IMAP access (SELECT readonly=True, FETCH
only). No deletes, moves, or any write actions on the mailbox.
"""

import email as _email
import imaplib
import os
from typing import Dict, List, Optional

from freelance_os.ingestion.email_parser import _SOURCE_DOMAIN_MAP, _parse_message

IMAP_PASSWORD_ENV = "FREELANCE_OS_IMAP_PASSWORD"

_ALERT_DOMAINS = set(_SOURCE_DOMAIN_MAP.keys())


def _is_job_alert(from_header: str) -> bool:
    from_lower = from_header.lower()
    return any(domain in from_lower for domain in _ALERT_DOMAINS)


def fetch_job_alert_emails(
    cfg: dict,
    max_emails: int = 50,
    source_override: Optional[str] = None,
) -> List[Dict]:
    """Fetch and parse recent job-alert emails via IMAP (READ-ONLY).

    Config keys: cfg["imap"]["host"], cfg["imap"]["user"],
    cfg["imap"]["mailbox"] (default "INBOX").
    Password is read from env var FREELANCE_OS_IMAP_PASSWORD.

    Returns list of job lead dicts (same format as email_parser).
    Raises RuntimeError with a helpful message on config/credential errors.
    """
    imap_cfg = cfg.get("imap", {})
    host = imap_cfg.get("host")
    user = imap_cfg.get("user")
    mailbox_name = imap_cfg.get("mailbox", "INBOX")
    password = os.environ.get(IMAP_PASSWORD_ENV)

    if not host or not user:
        raise RuntimeError(
            "IMAP config missing: add [imap] host and user to settings.toml. "
            f"Set password via env var {IMAP_PASSWORD_ENV}."
        )
    if not password:
        raise RuntimeError(
            f"IMAP password not set. Export {IMAP_PASSWORD_ENV}=<app-password>. "
            "Use an app-specific password, not your main account password."
        )

    conn = imaplib.IMAP4_SSL(host)
    try:
        conn.login(user, password)
        conn.select(mailbox_name, readonly=True)

        typ, data = conn.search(None, "ALL")
        if typ != "OK":
            raise RuntimeError(f"IMAP search failed: {typ}")

        uids = data[0].split() if data and data[0] else []
        uids = uids[-max_emails:]

        jobs: List[Dict] = []
        for uid in uids:
            typ, msg_data = conn.fetch(uid, "(RFC822)")
            if typ != "OK" or not msg_data:
                continue
            item = msg_data[0]
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            raw = item[1]
            if not isinstance(raw, bytes):
                continue
            msg = _email.message_from_bytes(raw)
            from_header = msg.get("From", "")
            if not _is_job_alert(from_header):
                continue
            jobs.extend(_parse_message(msg, source_override))

    finally:
        try:
            conn.logout()
        except Exception:
            pass

    return jobs
