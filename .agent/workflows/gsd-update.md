---
description: Check for GSD updates and install if available.
---
## Step 1: Detect Current Version

Check `.gemini/get-shit-done/VERSION` or `.claude/get-shit-done/VERSION`.

## Step 2: Check Latest

Run `npm view get-shit-done-cc version`.

## Step 3: Compare & Show Changelog

If a newer version exists, show "What's New" and warn that `./.gemini/get-shit-done/` will be wiped and replaced.

## Step 4: Confirm & Update

If user confirms, run `npx get-shit-done-cc --global` (or --local).

## Step 5: Post-Update

Advise user to restart the agent to pick up new commands.
