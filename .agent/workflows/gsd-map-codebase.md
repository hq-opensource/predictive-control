---
description: Orchestrate parallel codebase mapper agents to analyze codebase and produce structured documents.
---
## Philosophy

Dedicated mapper agents analyze specific focus areas and write documents directly to `.planning/codebase/`. The orchestrator summarizes the results.

## Step 1: Resolve Model Profile

Read model profile for agent spawning (default: balanced).

## Step 2: Check Existing

Check if `.planning/codebase/` exists. If so, ask:
- Refresh (Delete & Remap)
- Update (Specific documents)
- Skip

## Step 3: Create Structure

Create `.planning/codebase` directory. Expected files:
- `STACK.md`, `INTEGRATIONS.md`, `ARCHITECTURE.md`, `STRUCTURE.md`, `CONVENTIONS.md`, `TESTING.md`, `CONCERNS.md`.

## Step 4: Spawn Agents

Spawn 4 parallel `gsd-codebase-mapper` agents:
1. **Tech Focus:** Writes `STACK.md`, `INTEGRATIONS.md`.
2. **Architecture Focus:** Writes `ARCHITECTURE.md`, `STRUCTURE.md`.
3. **Quality Focus:** Writes `CONVENTIONS.md`, `TESTING.md`.
4. **Concerns Focus:** Writes `CONCERNS.md`.

## Step 5: Collect Confirmations

Wait for all 4 agents to complete. Collect confirmations (file paths and line counts).

## Step 6: Verify Output

Check that all 7 documents exist and are not empty.

## Step 7: Scan for Secrets

**CRITICAL SECURITY CHECK:** Scan generated documents for API keys or tokens. If found, pause and ask the user to review.

## Step 8: Commit & Offer Next

Commit the codebase map to git. Present summary and suggest `/new-project` next.
