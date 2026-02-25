---
description: Run a quick, simplified project initialization or status check.
---
## Philosophy

**Speed first.** Skip research, skip heavy questioning. Get to work NOW.

## Route A: New Project (Quick Start)

If `.planning/` doesn't exist:
1. Ask "What are we building?"
2. Create `PROJECT.md` with basic info.
3. Create `STATE.md` (started).
4. Create `ROADMAP.md` with 3-5 inferred phases.
5. Suggest `/gsd:discuss-phase 1`.

## Route B: Status Check (Quick Progress)

If `.planning/` exists:
1. Read `STATE.md`.
2. Show progress bar.
3. Show current phase/plan.
4. Suggest next command.

## Route C: Quick Plan

If argument is a phase number:
1. Generate 2-3 basic plans for the phase.
2. Skip verification.
3. Suggest `/gsd:execute-phase {N}`.
