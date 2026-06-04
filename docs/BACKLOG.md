# Backlog — freelance-os

Deferred polish, known limitations, and tuning items (captured 2026-06-04).
These feed the autonomous build pipeline and are also tracked as session tasks.

## Polish
- **Proposal template grammar** — draft generator emits "a authentication" / "a
  implementation" (no a/an agreement) and a trailing ".." after the proof point.
  Fix article selection + punctuation in `proposal/templates.py` +
  `proposal/draft_generator.py`.
- **Console Unicode glitch** — `lead list` / `client list` render mojibake on the
  Windows cp1252 console (stdout encoding — separate from the file utf-8 fix).
  Force utf-8 stdout or use ASCII-safe table characters.
- **Lead client-name parsing** — `add-text` doesn't extract a client name from a
  bare paste ("Unknown Client"). Improve the manual parser or add a `--client` flag.

## Tuning
- **Scoring is conservative on sparse input** — a strong lead scores low (46-58)
  because 6 of 8 §10.1 factors can't be inferred from raw text. Addressed by the
  metric-tuning console + optionally prompting for structured fields (client
  rating, budget-verified, urgency) at intake.

## Tech debt
- **datetime.utcnow() deprecation** (136 warnings) — modernize to
  `datetime.now(datetime.UTC)` across models/reports.

## Known limitations
- **tmux / execution harness is POSIX-only** — script *generation* is
  cross-platform, but `chmod +x` / running needs Linux/macOS/WSL; the exec-bit
  test is skipped on Windows. Revisit for native-Windows/WSL support if wanted.

## Out of MVP scope (PRD §5.2 long-term)
- Official Upwork API adapter, Gmail/IMAP ingestion, Fiverr export, Contra /
  LinkedIn CRM, portfolio memory layer, proposal A/B tracking, win/loss
  analytics, pricing recommendation engine, deeper multi-agent execution harness,
  local dashboard / Textual TUI.
