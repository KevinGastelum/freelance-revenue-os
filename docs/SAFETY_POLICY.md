# Safety Policy — Freelance Revenue OS

**Core principle: AI prepares. Human commits.**

---

## Prohibited Automation (PRD section 2.1)

The following must never be built, added, or dispatched:

- Stealth browser automation of any kind
- Residential proxy rotation
- CAPTCHA solving or bypassing
- Browser fingerprint spoofing
- Automated login to freelance platforms (Upwork, Fiverr, Contra, LinkedIn, etc.)
- Automated authenticated scraping
- Automated proposal submission
- Automated platform messaging
- Automated order delivery
- Automated milestone or payment actions
- Any feature designed to bypass anti-bot systems
- Any feature that simulates human browsing, typing cadence, mouse movement, or session behavior to evade detection

---

## Allowed Automation (PRD section 2.2)

The system may support:

- Manual URL intake (user provides URLs)
- Email alert parsing from user-exported files
- Official API integration where the platform permits it
- User-exported CSV/JSON imports
- Public RSS/API ingestion where permitted by the platform
- Lead scoring and deduplication (local computation only)
- Proposal drafting (output is draft-only; user must copy and send manually)
- Portfolio matching
- Risk detection
- Manual approval queues
- Local client workspace creation
- Git worktree setup (local only; no auto-push)
- Status update drafting
- Delivery package generation (marked DRAFT ONLY)
- README and changelog generation
- QA checklist generation
- Reminder and task generation

---

## Human Approval Rule (PRD section 2.3)

All platform write actions must be performed manually by the human.

The system may generate text and display it to the user, but the user must copy, edit, and submit it manually.

Actions that must always be manual:

- Submit proposal
- Send message
- Accept contract
- Decline invitation
- Deliver order
- Request milestone release
- Send invoice
- Move communication off-platform
- Modify platform account settings

---

## Configuration Enforcement

The following safety flags in `config/settings.toml` **must always be false**:

```toml
[safety]
allow_browser_automation = false
allow_auto_submit = false
allow_auto_message = false
allow_scraping = false
require_human_approval = true
```

The application will refuse to start if any prohibited flag is set to `true`.
This is enforced in `src/freelance_os/config.py` via `validate_safety()`.

---

## Delivery Message Policy

Any generated delivery message, proposal draft, or client communication must be
clearly marked:

```
DRAFT ONLY — USER MUST REVIEW AND SEND MANUALLY
```

The system must never send, submit, or transmit any content to a platform
on behalf of the user.
