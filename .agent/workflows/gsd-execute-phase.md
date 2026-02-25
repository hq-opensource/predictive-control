---
description: Execute all plans in a phase using wave-based parallel execution.
---
## Core Principle

The orchestrator coordinates, delegates execution to subagents. Each subagent loads full execution context.

## Step 1: Resolve Model Profile

Read `model_profile` from `.planning/config.json`. Default to "balanced".

## Step 2: Load Project State

Read `.planning/STATE.md` and `config.json` to load project context, parallelization settings, and branching strategy.

## Step 3: Handle Branching

If branching strategy is set (phase or milestone), create or switch to the appropriate git branch.

## Step 4: Validate Phase

Confirm phase directory exists and contains plan files.

## Step 5: Discover Plans

List all plans, filter out completed ones (those with `SUMMARY.md`). Group plans by `wave` number from their frontmatter.

## Step 6: Execute Waves

Execute each wave in sequence. Plans within a wave run in parallel if `parallelization: true` in config.

**For each wave:**
1. Describe what's being built.
2. Inline file contents (Plan, State, Config) and spawn agents using `Task`.
3. Wait for all agents in wave to complete.
4. Spot-check results (verify files exist, check git log, check for failure markers).
5. Handle failures: If any agent fails, ask user whether to continue or stop.

## Step 7: Checkpoint Handling (for Non-autonomous Plans)

If a plan has `autonomous: false`, it will hit checkpoints requiring user input/action.
1. Orchestrator presents checkpoint details (verify, decision, or action).
2. User responds.
3. Orchestrator spawns a fresh continuation agent with user's feedback.

## Step 8: Aggregate & Verify

1. Aggregate results from all waves.
2. Spawn `gsd-verifier` to check phase goal achievement.
3. If passed: proceed. If gaps found: offer `/plan-phase {phase} --gaps`.

## Step 9: Update Roadmap & Commit

Update `ROADMAP.md` status to "Complete". Commit roadmap, state, and verification reports.

---
## ▶ Next Up
If more phases: /plan-phase {next}
If milestone complete: /complete-milestone
---
