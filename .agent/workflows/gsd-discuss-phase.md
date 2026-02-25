---
description: Extract implementation decisions that downstream agents need. Identify gray areas, discuss with user, and capture context.
---
## Philosophy

**User = founder/visionary. Agent = builder.**

Your job is to capture decisions clearly enough that downstream agents (researchers, planners) can act on them without asking the user again.

## Step 1: Validate Phase

Phase number from argument (required). Load `.planning/ROADMAP.md`, find phase entry. If not found, exit.

## Step 2: Check Existing

Check if `CONTEXT.md` already exists in phase directory. If it does, ask user:
- Update it
- View it
- Skip

## Step 3: Analyze Phase

Determine:
1. **Domain boundary** — What capability is this phase delivering?
2. **Gray areas by category** — UI, UX, Behavior, Empty States, Content. Identify 1-2 specifics.
3. **Skip assessment** — If no meaningful gray areas, it may not need discussion.

## Step 4: Present Gray Areas

State the domain boundary and use `AskUserQuestion` (multi-select) to let user pick which areas to discuss.

## Step 5: Discuss Areas

For each selected area, ask up to 4 questions. Each answer should inform the next question. After 4 questions, check if more are needed or move to next area.

**Scope Creep Handling:** If user suggests something outside phase scope, redirect to "Deferred Ideas".

## Step 6: Write Context

Create `CONTEXT.md` in the phase directory:
- Domain Boundary
- Implementation Decisions (by category)
- Claude's Discretion (areas where user said "you decide")
- Specific Ideas/References
- Deferred Ideas

## Step 7: Confirm & Commit

Show summary and next steps. Commit the context file to git.

---
## ▶ Next Up
/plan-phase {N}
---
