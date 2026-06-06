<!--
# Safety Policy — Freelance Revenue OS

## Core Principle

> AI prepares. Human commits.

This system is designed to reduce freelance workload without risking platform bans or violating terms of service.

## Prohibited Automation (Non-Negotiable)

The following are **permanently prohibited** and will never be implemented:

1. **Stealth browser automation** — no headless browsing, mouse simulation, or bot-like behavior
2. **Residential proxy rotation** — no IP rotation or geo-spoofing
3. **CAPTCHA solving or bypassing** — no CAPTCHA solving services or workarounds
4. **Browser fingerprint spoofing** — no user-agent manipulation or fingerprint masking
5. **Automated platform login** — no login automation to Upwork, Fiverr, or any freelance platform
6. **Authenticated scraping** — no scraping of authenticated dashboards or profile pages
7. **Automated proposal submission** — no auto-submitting proposals or bids
8. **Automated platform messaging** — no auto-sending messages on any platform
9. **Automated order delivery** — no auto-delivering work or triggering milestone releases
10. **Automated payment actions** — no requesting payments, releasing milestones, or issuing invoices automatically

## Enforced in Code

The config loader raises `ConfigError` if any of the following are set to `true`:

- `safety.allow_auto_submit`
- `safety.allow_browser_automation`
- `safety.allow_auto_message`
- `safety.allow_scraping`

This is a hard enforcement — the application refuses to start with unsafe configuration.

## Allowed Automation

The system may safely automate:

- Storing leads in a local database
- Scoring leads using configurable rules
- Generating proposal drafts (for human review and manual submission)
- Creating local client workspaces and markdown files
- Generating delivery package content (for human review and manual delivery)
- Generating reports from local data
- Generating shell scripts for tmux sessions (user runs them manually)

## Human Approval Requirement

All platform write actions require the human to:

1. Review the generated content
2. Copy and edit as needed
3. Submit manually through the platform UI

The system will never submit, send, or deliver on behalf of the user.

## Delivery Message Safety

Delivery message drafts are always clearly marked:

```
DRAFT ONLY - USER MUST REVIEW AND SEND MANUALLY
```

This marking cannot be removed by configuration.

## Reporting Violations

If any feature is found to violate these policies, it should be reported immediately and removed.
No compliance exception will be made for convenience or business reasons.

---

*This policy is derived from PRD section 2 (Non-Negotiable Safety and Compliance Rules).*
-->
