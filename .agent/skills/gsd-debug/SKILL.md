---
name: gsd-debug
description: Systematic debugging with persistent state across context resets.
---
# GSD Debug Skill

This skill provides patterns for investigating, fixing, and verifying bugs while maintaining a persistent "debug brain" in `.planning/debug/`.

## 1. Lifecycle
- **Gathering**: Collect symptoms (expected vs actual), error messages, and reproduction steps.
- **Investigating**: Formulate hypotheses, test them, and record evidence.
- **Fixing**: Apply the fix once the root cause is confirmed.
- **Verifying**: Confirm the fix works and doesn't introduce regressions.

## 2. Debug Brain (.planning/debug/[slug].md)
Maintain a structured file to ensure continuity across context resets.
- **Hypothesis tracking**: Record what was tested and what was eliminated.
- **Evidence log**: Store facts discovered (logs, file states, etc.).
- **Outcome**: Document the confirmed root cause and the verified fix.

## 3. Rules
- **Atomic Commits**: Commit the fix and the updated debug file together.
- **No Narrative**: Use structured data (YAML/Markdown lists) for evidence to keep context low.
- **Resume First**: Always read the existing debug file before resuming work after a `/clear`.

## 4. Subagents
Detailed agent definitions are located in `resources/agents/`:
- **debugger.md**: Investigates bugs using the scientific method.
