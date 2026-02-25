---
description: Systematic debugging with persistent state across context resets.
---
## Step 0: Resolve Model Profile

Determine model for `gsd-debugger` (default: balanced).

## Step 1: Check Active Sessions

If active sessions exist and no arguments provided:
- List sessions and offer to resume.

## Step 2: Gather Symptoms (for new issues)

Ask user:
1. Expected behavior
2. Actual behavior
3. Error messages
4. Timeline (when did it start?)
5. Reproduction steps

## Step 3: Spawn Debugger Agent

Spawn `gsd-debugger` subagent. It will write an investigation log to `.planning/debug/{slug}.md`.

## Step 4: Handle Return

- **ROOT CAUSE FOUND:** Display and offer fix (fix now, plan fix, or manual).
- **CHECKPOINT REACHED:** Surface questions to user and spawn continuation agent.
- **INCONCLUSIVE:** Show eliminated hypotheses and offer deeper investigation.
