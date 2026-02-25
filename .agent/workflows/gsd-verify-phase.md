---
description: Verify phase goal achievement through goal-backward analysis.
---
## Core Principle: Task completion ≠ Goal achievement

Verification starts from the outcome: What must be TRUE? What must EXIST? What must be WIRED?

## Step 1: Load Context

Read `ROADMAP.md` (goal), `REQUIREMENTS.md`, and phase `SUMMARY.md` files.

## Step 2: Establish Must-Haves

- **Option A:** Use `must_haves` from `PLAN.md` frontmatter if available.
- **Option B (Goal-backward):** Derive truths (behaviors), artifacts (files), and key links (connections) from the phase goal.

## Step 3: Verify Levels

1. **Existence:** Does the file exist?
2. **Substantive:** Is it a real implementation or just a stub? (Check length, stub patterns, exports).
3. **Wired:** Is it imported and used in the system?

## Step 4: Verify Key Links

Check critical connections:
- Component -> API (fetch/axios calls)
- API -> Database (queries)
- Form -> Handler (working onSubmit)
- State -> Render (variables actually displayed)

## Step 5: Scan Anti-Patterns

Check for TODOs, HACKs, placeholder text ("lorem ipsum"), or log-only implementations.

## Step 6: Determine Status

- **passed:** Goal achieved.
- **gaps_found:** Critical stubs or wiring failures.
- **human_needed:** Automated checks passed, but needs visual/flow validation.

## Step 7: Fix Recommendations

If gaps found, group them into focused fix plans with specific tasks and actions. Create `VERIFICATION.md` report.
