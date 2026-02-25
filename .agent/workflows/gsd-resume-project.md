---
description: Instantly restore full project context so "Where were we?" has an immediate, complete answer.
---
## Step 1: Detect Project

Check for `.planning/STATE.md`, `ROADMAP.md`, and `PROJECT.md`.
- If NO project: Route to `/gsd:new-project`.
- If missing STATE.md: Offer to reconstruct it.

## Step 2: Load State

Read `STATE.md` and `PROJECT.md`.
Extract: Core value, current position, progress, recent decisions, pending todos, blockers, and session continuity notes.

## Step 3: Check Incomplete Work

- Check for `.continue-here.md` files (mid-plan resumption).
- Check for `PLAN.md` without `SUMMARY.md` (incomplete execution).
- Check for interrupted agents (via `agent-history.json` or tracker files).

## Step 4: Present Status

Show "PROJECT STATUS" banner with:
- Building: [Description]
- Phase/Plan: [Current Position]
- Progress: [Bar]
- Incomplete work or interrupted agents (if any).
- Pending todos and carried concerns.

## Step 5: Determine & Offer Next Action

- **Interrupted Agent?** -> Primary: Resume Agent.
- **Checkpoint found?** -> Primary: Resume from checkpoint.
- **Incomplete Plan?** -> Primary: Complete plan.
- **Phase ready to plan?** -> Primary: `/gsd:discuss-phase` or `/gsd:plan-phase`.
- **Phase ready to execute?** -> Primary: `/gsd:execute-phase`.

## Step 6: Route & Transition

Update `STATE.md` Session Continuity section. Present the selected command as "Next Up".
