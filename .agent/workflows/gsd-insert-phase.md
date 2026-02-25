---
description: Insert a decimal phase for urgent work between existing integer phases.
---
## Step 1: Parse Arguments

Expected: target integer phase + description.
Example: `/insert-phase 72 Fix critical bug`

## Step 2: Load Roadmap

Read `.planning/ROADMAP.md`. Error if not found.

## Step 3: Verify Target Phase

Check if the target integer phase exists in the roadmap.

## Step 4: Calculate Decimal Number

Find existing decimal phases (e.g., 72.1, 72.2) to determine the next one (72.(N+1)).

## Step 5: Create Resources

- Generate slug from description.
- Create directory: `.planning/phases/{decimal}-{slug}`.

## Step 6: Update Roadmap & State

- Insert the new phase entry in `ROADMAP.md` after the target phase.
- Mark it as `(INSERTED)`.
- Update `STATE.md` Roadmap Evolution section.

## Step 7: Completion

Report the new phase directory and suggest next step.

---
## ▶ Next Up
/plan-phase {decimal}
---
