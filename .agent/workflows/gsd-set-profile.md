---
description: Switch model profile for GSD agents (quality/balanced/budget).
---
## Objective

Quickly switch model profile to balance quality vs token cost.

## Profiles

- **quality:** Opus everywhere (high cost).
- **balanced:** Opus for planning, Sonnet for execution (default).
- **budget:** Sonnet for planning, Haiku for research/verification (low cost).

## Process

Update `model_profile` in `.planning/config.json`. Display model lookup table for the selected profile.
