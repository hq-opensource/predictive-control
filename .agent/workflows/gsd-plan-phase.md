---
description: Create detailed execution plan for a phase (PLAN.md) with verification loop.
---
## Step 1: Validate Environment

Error if `.planning/` missing. Resolve model profile from config.

## Step 2: Parse Args

Phase number (integer or decimal). Flags: `--research`, `--skip-research`, `--gaps`, `--skip-verify`.

## Step 3 & 4: Phase Setup

Validate phase against roadmap. Ensure phase directory exists. Load `CONTEXT.md` (MUST be passed to all downstream agents).

## Step 5: Handle Research

If research enabled and not skipped: spawn `gsd-phase-researcher` to investigate domain.

## Step 6: Spawn Planner

Spawn `gsd-planner` subagent.
**Context:** `STATE.md`, `ROADMAP.md`, `REQUIREMENTS.md`, `CONTEXT.md` (locked user decisions), and `RESEARCH.md`.
**Goal:** Create `PLAN.md` files with tasks, waves, and `must_haves`.

## Step 7: Verification Loop

Spawn `gsd-plan-checker` to verify plans against the phase goal and user context.
- If issues found: Revision loop (max 3 iterations).

## Step 8: Present Results

Show wave/plan breakdown. Suggest `/gsd-execute-phase {N}`.
