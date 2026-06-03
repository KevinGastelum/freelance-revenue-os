# Safety Policy — Freelance Revenue OS

## Core Principle

> **AI prepares. Human commits.**

This system is designed to assist — never to act autonomously on freelance platforms.

## Prohibited Automation

The following are permanently prohibited and will never be implemented:

- Stealth browser automation
- Residential proxy rotation
- CAPTCHA solving or bypassing
- Browser fingerprint spoofing
- Automated login to freelance platforms
- Automated authenticated scraping
- Automated proposal submission
- Automated platform messaging
- Automated order delivery
- Automated milestone or payment actions
- Any feature designed to bypass anti-bot systems
- Any feature that simulates human browsing behavior to evade detection

## What the System Does

The system generates **draft-only** outputs for human review:

- Lead scoring and analysis
- Proposal drafts (never submitted automatically)
- Client workspace files
- Delivery message drafts (clearly marked DRAFT ONLY)
- Weekly performance reports

## Config Safety Enforcement

The config loader will **raise an error** if any of the following are set to `true`:

- `allow_auto_submit`
- `allow_browser_automation`
- `allow_auto_message`
- `allow_scraping`

This is enforced at startup and cannot be bypassed without modifying source code.

## Human Approval Requirement

All platform write actions must be performed manually by the user:

- Submit proposal → user copies draft and submits manually
- Send message → user copies draft and sends manually
- Deliver order → user sends delivery message manually
- Release milestone → user triggers via platform UI

## Audit Trail

All generated text is stored locally with timestamps. No data is sent to external
services automatically. The user controls all external interactions.
