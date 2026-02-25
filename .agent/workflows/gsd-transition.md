---
description: Mark current phase complete and advance to next. Evolves PROJECT.md with learnings.
---
## Required Reading

- `STATE.md`, `PROJECT.md`, `ROADMAP.md`
- Current phase's `PLAN.md` and `SUMMARY.md` files.

## Step 1: Verify Completion

Check that all plans in the current phase have matching summaries.
- **If incomplete:** Warn user. Skipping plans is destructive and requires confirmation.

## Step 2: Update Roadmap

- Mark current phase as `[x] Complete`.
- Add completion date.
- Update progress table.
- Mark next phase as `[ ] Not started`.

## Step 3: Evolve Project (Core Step)

Read phase summaries to extract learnings:
1. **Validate Requirements:** Move shipped requirements from "Active" to "Validated".
2. **Invalidate Requirements:** Move wrong/unnecessary requirements to "Out of Scope".
3. **Emerge Requirements:** Add new discoveries to "Active".
4. **Log Decisions:** Add new decisions to the "Key Decisions" log in `PROJECT.md`.
5. **Update Description:** If product has changed, update "What This Is".

## Step 4: Update State

- Increment current phase number in `STATE.md`.
- Reset plan to "Not started".
- Set status to "Ready to plan".
- Update progress bar and recent decisions/blockers.

## Step 5: Determine Milestone Status

- **More phases remain:** Suggest `/gsd:discuss-phase {next}`.
- **Milestone complete:** Suggest `/gsd:complete-milestone`.
