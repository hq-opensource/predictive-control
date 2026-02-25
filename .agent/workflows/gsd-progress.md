---
description: Check project progress, summarize recent work, and route to the next action.
---
## Step 1: Verify Structure

Ensure `.planning/` exists. If not, suggest `/new-project`.

## Step 2: Load Context

Read `STATE.md`, `ROADMAP.md`, `PROJECT.md`, and `config.json`.

## Step 3: Gather Recent Work

Find the 2-3 most recent `SUMMARY.md` files. Extract accomplishments and decisions.

## Step 4: Parse Current Position

Calculate total plans, completed plans, and remaining plans from `STATE.md`. Check for pending todos or active debug sessions.

## Step 5: Present Status Report

Show progress bar, profile, recent work, current position, key decisions, blockers, and pending items.

## Step 6: Route to Next Action

Route based on current state:
- **UAT gaps found:** Suggest `/plan-phase {phase} --gaps`.
- **Unexecuted plans exist:** Suggest `/execute-phase {phase}`.
- **Phase needs planning:** Suggest `/discuss-phase {phase}` or `/plan-phase {phase}`.
- **Phase complete, more remain:** Suggest `/discuss-phase {next}`.
- **Milestone complete:** Suggest `/complete-milestone`.
- **Between milestones:** Suggest `/new-milestone`.
