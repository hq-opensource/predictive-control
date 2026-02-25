---
description: Remove an unstarted future phase from the roadmap and renumber subsequent phases.
---
## Step 1: Parse Arguments

Phase number required.

## Step 2: Load State

Read `STATE.md` and `ROADMAP.md`.

## Step 3 & 4: Validate Phase

Ensure phase exists and is a future phase (not current or completed). Ensure no `SUMMARY.md` files exist for it.

## Step 5: Gather Info

Identify phase name, directory, and all subsequent phases needing renumbering.

## Step 6: Confirm Removal

Present deletion and renumbering plan to user for confirmation.

## Step 7, 8, & 9: Delete & Renumber

- Delete the target phase directory.
- Renumber subsequent directories in descending order.
- Renumber files (PLAN.md, etc.) inside those directories.

## Step 10, 11, & 12: Update Docs

- Update `ROADMAP.md` (remove section, renumber headings and tables, update dependencies).
- Update `STATE.md` (phase count, progress percentage).
- Update internal phase references in remaining files via grep/replacement.

## Step 13: Commit & Finish

Commit changes and show updated project status.
