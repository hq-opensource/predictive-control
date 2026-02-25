---
description: Research how to implement a phase. Spawns gsd-phase-researcher with phase context.
---
## Step 0: Resolve Model Profile

Determine model for `gsd-phase-researcher` (default: balanced).

## Step 1: Normalize and Validate Phase

Phase number required. Check `ROADMAP.md` for phase existence.

## Step 2: Check Existing Research

If `RESEARCH.md` already exists in the phase directory, ask user:
- Update
- View
- Skip

## Step 3: Gather Phase Context

Read `ROADMAP.md`, `REQUIREMENTS.md`, `CONTEXT.md` (if exists), and `STATE.md` decisions.

## Step 4: Spawn Researcher

Spawn `gsd-phase-researcher` with the gathered context. Objective: Research implementation approach for the phase.

## Step 5: Handle Return

- **RESEARCH COMPLETE:** Display summary. Offer: Plan, Dig deeper, Review, or Done.
- **CHECKPOINT REACHED:** Present to user, spawn continuation if needed.
- **INCONCLUSIVE:** Show attempts, offer to add context or try a different mode.
