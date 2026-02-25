---
name: gsd-git
description: Patterns and guidelines for git operations within the GSD framework.
---

# GSD Git Skill

Follow these patterns for all git operations to ensure a clean, outcome-oriented history.

## Commit Points
- **Initialization**: Commit `PROJECT.md` and initial planning docs.
- **Tasks**: Commit each task immediately after completion.
- **Plan Completion**: Metadata commit for `SUMMARY.md`, `STATE.md`, and `ROADMAP.md`.
- **Handoff**: `wip:` commit when pausing mid-phase.

## Commit Formats
- `feat({phase}-{plan}): {description}`
- `fix({phase}-{plan}): {description}`
- `test({phase}-{plan}): {description}`
- `refactor({phase}-{plan}): {description}`
- `docs({phase}-{plan}): {description}`

## Branching Strategies
- **None**: Commit directly to the current branch.
- **Phase**: Create a branch per phase (`gsd/phase-{N}-{slug}`).
- **Milestone**: Create a branch per milestone (`gsd/{version}-{slug}`).
