---
name: warren-steer-recover
description: Steer, cancel, diagnose, or recover a Warren run.
---

# Warren Steer and Recover

Use this skill when a Warren run is stuck, drifting, failed, or unsafe.

## Procedure

1. Identify the run id.
2. Stream events: `bash scripts/wr-events.sh <run-id>`
3. If the agent is close but needs correction:
   `bash scripts/wr-steer.sh <run-id> "<clear bounded steering message>"`
4. If the run is destructive, leaking secrets, or clearly wrong:
   `bash scripts/wr-cancel.sh <run-id>`
5. Check Warren health: `bash scripts/wr-health.sh`
6. If the CLI exists: `warren doctor`
7. Inspect project config: `.warren/config.yaml`, `.warren/triggers.yaml`,
   `.warren/preview.yaml`
8. Summarize root cause, likely fix, and the safe next action.

## Steering Message Guidelines

Short, imperative, scoped. Example:

"Stop modifying auth. Only add tests for the existing lead scorer and summarize
failures."

## Safety

Cancel rather than steer if the run touches secrets/`.env`, deletes large
directories, rewrites history, ignores scope, or tries to add prohibited platform
automation (docs/PRD.md section 2).
