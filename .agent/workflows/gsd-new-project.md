---
description: Initialize a new project with deep context gathering and PROJECT.md.
---
## Phase 1: Setup & Detection

Ensure `.planning/` doesn't already exist. Initialize git if needed. Detect existing codebases for brownfield mapping.

## Phase 2: Deep Questioning

Ask "What do you want to build?". Follow threads to challenge vagueness and surface assumptions. Aim for absolute clarity before moving to docs.

## Phase 3: Create PROJECT.md

Synthesize all context: vision, core value, requirements (as hypotheses), keys decisions, and constraints.

## Phase 4: Workflow Preferences

Interactively set:
- Mode (YOLO vs Interactive)
- Planning Depth
- Parallelization
- Git tracking preferences
- Agent toggles (Researcher, Checker, Verifier)
- Model Profile

## Phase 5: Research & Requirements

- Optional domain research (spawns 4 parallel agents).
- Generate `REQUIREMENTS.md` with REQ-IDs and priority scoping (v1/v2/out-of-scope).

## Phase 6: Roadmap & State

Spawn `gsd-roadmapper` to create `ROADMAP.md` and initialize `STATE.md`. Every requirement must map to a phase.

## Phase 7: Completion

Report all created artifacts and suggest `/gsd-discuss-phase 1`.
