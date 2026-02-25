---
description: Create context handoff when pausing work mid-phase.
---
## Step 1: Gather State

Collect: current phase/plan/task, work done vs remaining, recent decisions, blockers, files modified, and "next action" thoughts.

## Step 2: Write Handoff

Create `.planning/phases/{XX-name}/.continue-here.md`. Be specific enough for a fresh agent to resume immediately.

## Step 3: Update State & Commit

Update `STATE.md` session continuity. Commit the handoff as a WIP commit.

## Step 4: Confirm

Display current status and location of the handoff file.
