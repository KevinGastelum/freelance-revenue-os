# Build Spec — `freelance-os pull`

Turnkey spec so reopening = execute. Build task #1 (see `docs/HANDOFF.md`).

## Goal
One command that returns a **ranked, drafted shortlist** of freelance gigs pulled from
legitimate public sources — ranked by AI-leverage margin, reputation-aware, stack-agnostic.

## Sources (v1 — public, no auth)
- Remotive — `GET https://remotive.com/api/remote-jobs` (proven)
- RemoteOK — `GET https://remoteok.com/api` (set a UA; first array element is a notice)
- Jobicy — `GET https://jobicy.com/api/v2/remote-jobs`
- HN — `https://hn.algolia.com/api/...` (monthly "Seeking freelancer" thread; proven)

v2: Himalayas, We Work Remotely RSS, Freelancer.com official API, operator's IMAP alert inbox.

## Pipeline
fetch (per source) -> normalize -> dedupe (by url) -> score -> rank -> draft top-K -> output.

## Lead schema (normalize every source to this)
- required: `source, url, title, description, budget{amount, currency, type: fixed|hourly}`
- optional: `skills[], posted_at (ISO), client{country, rating, payment_verified, total_spend, hires}, location, remote`

## Scoring — AI-leverage margin (NOT stack match)
Per lead:
- `effort_hours` — estimate from the description (scope keywords, deliverable size). Heuristic
  v1; LLM-assisted v2. Bounded / well-documented / small -> lower.
- `confidence` — spec clarity, budget present, client verified.
- `budget_usd` — normalize currency; for hourly, multiply by a configurable assumed-hours figure.
- `margin = budget_usd / max(effort_hours, 0.25)`.
- `reputation_value` — high for low-risk, easy-win, review-generating, first-client gigs.
- `final_score = w_margin*norm(margin) + w_rep*reputation_value + w_conf*confidence`.
  **Reputation mode** (default ON while the account has few reviews): raise `w_rep` so a cheap,
  easy, review-building gig still ranks near the top. Never down-rank for low $ alone.
- `verdict` — one line, e.g. `quick buck: ~N h, $X, conf M, rep+`.

Do **not** include any stack/skill-match term in the score.

## Output
- ranked table: title, source, $, ~effort, margin, verdict, url
- top-K draft applications (reuse `src/freelance_os/proposal/draft_generator.py`)
- optional persist to SQLite (reuse `models.Lead`, `db.py`), dedupe by url

## CLI
`freelance-os pull [--source ...] [--limit N] [--reputation-mode/--no-reputation-mode] [--min-margin X] [--json]`

Register in `src/freelance_os/cli.py`. New code: `src/freelance_os/ingestion/pull.py` +
`src/freelance_os/scoring/margin.py`.

## Constraints
- Cross-platform: utf-8, pathlib, stdlib `urllib` — NO scraping/browser libs, no new heavy deps.
- Additive — don't break the existing suite; add tests under `tests/`.
- Acceptance: `freelance-os pull` returns >=1 scored lead from a live API; `uv run pytest -q` green.
