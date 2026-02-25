---
description: Orchestrate parallel debug agents to investigate UAT gaps and find root causes.
---
## Core Principle

**Diagnose before planning fixes.**

UAT tells us WHAT is broken (symptoms). Debug agents find WHY (root cause). /plan-phase --gaps then creates targeted fixes based on actual causes.

## Step 1: Parse Gaps

**Extract gaps from UAT.md:**

Read the "Gaps" section (YAML format) and the corresponding tests.

## Step 2: Report Plan

**Report diagnosis plan to user:**

```
## Diagnosing {N} Gaps

Spawning parallel debug agents to investigate root causes...
```

## Step 3: Spawn Agents

**Spawn debug agents in parallel:**

For each gap, spawn a task:

```
Task(
  prompt=filled_debug_subagent_prompt,
  subagent_type="general-purpose",
  description="Debug: {truth_short}"
)
```

## Step 4: Collect Results

Parse each return to extract:
- root_cause: The diagnosed cause
- files: Files involved
- debug_path: Path to debug session file
- suggested_fix: Hint for gap closure plan

## Step 5: Update UAT

**Update UAT.md gaps with diagnosis:**

For each gap in the Gaps section, add artifacts and missing fields.

**Commit the updated UAT.md:**
```bash
git add ".planning/phases/XX-name/{phase}-UAT.md"
git commit -m "docs({phase}): add root causes from diagnosis"
```

## Step 6: Report Results

Display results table and hand off to verify-work orchestrator.
