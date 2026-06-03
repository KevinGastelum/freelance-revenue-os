---
name: warren-project-setup
description: Prepare or audit this repository for Warren sandboxed agent runs.
---

# Warren Project Setup

Use this skill when this repo needs to be initialized, audited, or repaired for
Warren. Operator shell here is Git Bash; the `warren` CLI is not on PATH (Warren
is the Docker container + UI), so prefer `scripts/wr-*.sh` and the UI.

## Procedure

1. Inspect `.warren/` (config.yaml, triggers.yaml, preview.yaml, pr-template.md).
2. Check `CLAUDE.md` has the Warren Operating Contract.
3. Check `docs/warren-runbook.md` and `docs/warren-project-contract.md`.
4. Check `scripts/wr-*.sh` exist and are executable (`bash -n` to lint).
5. Run `bash scripts/wr-health.sh` if `WARREN_BASE_URL` is reachable (liveness is
   unauthenticated; readiness needs `WARREN_API_TOKEN`).
6. Run `warren doctor` only if the CLI exists.
7. Verify `.warren/config.yaml` keeps `mergeStrategy: manual` and `defaultBranch: main`.
8. Verify `.warren/triggers.yaml` does not enable unwanted cron automation.
9. Verify `.warren/preview.yaml` matches the project's dev server (none yet).
10. Verify `.warren/pr-template.md` reminds humans to review before merge.
11. Confirm `.claude/settings.json` wires `warren-guard.js` and `.gitignore`
    ignores `.env*` and `.warren/tmp/`.
12. Summarize missing or repaired pieces.

## Do Not

- Do not print secrets or `.env` contents.
- Do not overwrite existing configs without preserving content.
- Do not enable scheduled triggers without explicit human approval.
