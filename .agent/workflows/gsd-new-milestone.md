---
description: Orchestrate new-milestone from context loading through roadmap approval.
---
## Required Reading

- Questioning protocols
- UI/Brand references
- Project & Requirements templates

## Phase 1: Load Context

Load `PROJECT.md`, `STATE.md`, `MILESTONES.md`, and `config.json`.

## Phase 2: Gather Milestone Goals

- If `MILESTONE-CONTEXT.md` exists: Use established scope.
- Otherwise: Ask "What do you want to build next?" and explore features/priorities.

## Phase 3: Determine Milestone Version

Suggest next version (v1.0 -> v1.1 or v2.0).

## Phase 4 & 5: Update project docs

Update "Current Milestone" and "Active Requirements" in `PROJECT.md`. Update `STATE.md` status.

## Phase 6 & 6.5: Cleanup & Resolve Models

Delete temporary context files. Resolve models for research and roadmapping agents.

## Phase 7: Research Decision

Ask user if they want to research the domain ecosystem first.
- If research: Spawn 4 parallel researchers (Stack, Features, Architecture, Pitfalls).

## Phase 8: Define Requirements

Generate `REQUIREMENTS.md` with checkboxed requirements for this milestone, future requirements, and out-of-scope items.

## Phase 9: Create Roadmap

Spawn `gsd-roadmapper` to derive phases from requirements. Map every requirement to exactly one phase. Present roadmap for user approval.

## Phase 10: Done

Commit all documents and suggest `/discuss-phase {N}` to start work.
