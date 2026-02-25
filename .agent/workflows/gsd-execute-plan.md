---
description: Execute a specific plan (PLAN.md) and create the outcome summary (SUMMARY.md).
---
## Required Reading

- `.planning/STATE.md`
- `.planning/config.json`
- Git integration references

## Step 1: Resolve Model Profile

Determine model for `gsd-executor` from config.

## Step 2: Load Project State

Read `STATE.md` for project context, decisions, and blockers.

## Step 3: Identify Plan

Find the first plan in the current phase without a `SUMMARY.md`.

## Step 4: Parse Segments

Intelligently segment the plan by checkpoints.
- No checkpoints: Fully autonomous (1 subagent).
- Checkpoints: Parse into segments. Determine if segments can run in subagents or must stay in main context (decision-dependent).

## Step 5: Execute Plan

Execute each task in the plan:
- **Auto Tasks:** Implement functionality. Check for TDD flag. Commit each task atomically.
- **TDD Flow:** RED (fail test) -> GREEN (pass) -> REFACTOR cycle.
- **Auth Gates:** If auth error, pause, ask user to auth, then retry.
- **Deviations:**
  - Rule 1 (Bug): Auto-fix.
  - Rule 2 (Missing Critical): Auto-add.
  - Rule 3 (Blocking): Auto-fix.
  - Rule 4 (Architectural): STOP, ask user.

## Step 6: Create Summary

Create `{phase}-{plan}-SUMMARY.md`:
- Document accomplishments, key files created/modified, and decisions made.
- Document all deviations and timing data.
- Self-check: verify key files exist and git commits were made.

## Step 7: Update State & Roadmap

- Update `STATE.md` current position, progress bar, and session continuity.
- Update `ROADMAP.md` plan count and phase status.
- Commit metadata (Summary, State, Roadmap).

## Step 8: Offer Next

Check if more plans remain in the phase or if the milestone is complete. Present appropriate next command.
