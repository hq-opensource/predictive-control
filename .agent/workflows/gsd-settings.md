---
description: Configure GSD workflow toggles and model profile.
---
## Step 1: Ensure Config

Check/create `.planning/config.json` with defaults.

## Step 2: Present Interactively

Use `AskUserQuestion` to toggle:
- Model Profile (Quality/Balanced/Budget)
- Research (On/Off)
- Plan Check (On/Off)
- Execution Verifier (On/Off)
- Git Branching Strategy (None/Phase/Milestone)

## Step 3: Update & Confirm

Merge selections into `config.json`. Show final configuration table to user.
