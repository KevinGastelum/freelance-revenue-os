---
name: warren-plan-run
description: Use Warren with Seeds plans and optional Plot coordination.
---

# Warren Plan-Run

Use this skill when this repo has `.seeds/` and the user wants Warren to execute a
plan. NOTE: Seeds (`sd`) and Plot (`plot`) are not installed on this machine yet —
if they are absent, fall back to a single bounded `warren-dispatch` instead.

## Procedure

1. Verify `.seeds/` exists.
2. Check available Seeds commands: `sd plan list`, `sd ready`
3. Inspect the selected plan: `sd plan show <plan-id>`
4. If `.plot/` exists, inspect relevant plots: `plot list`, `plot show <plot-id>`
5. Dispatch the plan-run through the Warren API/CLI if the installed version
   supports it.
6. Monitor plan-run events.
7. Confirm each child seed completes and is verified before the next dispatches.
8. Do not force-close seeds unless the work is verified.

## Rule

For multi-step work, prefer a Seeds plan-run over a vague monolithic Warren
prompt. With no Seeds installed, decompose the work yourself and dispatch small,
bounded runs in sequence.
