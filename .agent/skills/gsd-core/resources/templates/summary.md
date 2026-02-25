# Summary Template
Template for `.planning/phases/XX-name/XX-YY-SUMMARY.md` — plan completion.

## File Template
```markdown
---
phase: XX-name
plan: YY
subsystem: [category]
tags: [tech]
requires:
  - phase: [prior]
    provides: [what]
provides:
  - [delivered]
affects: [keywords]
duration: Xmin
completed: YYYY-MM-DD
---

# Phase [X]: [Name] Summary

**[Substantive one-liner describing outcome]**

## Performance
- **Duration:** [time]
- **Tasks:** [N]
- **Files modified:** [N]

## Accomplishments
- [Outcome]

## Task Commits
1. **Task 1** - `[hash]` (type)

## Files Created/Modified
- `[path]` - [desc]

## Decisions Made
[Rationale]

## Deviations from Plan
None.

## Next Phase Readiness
[Ready status / blockers]
```
