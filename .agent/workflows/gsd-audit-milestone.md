---
description: Verify milestone achieved its definition of done.
---
## Step 0: Resolve Model Profile

@./.gemini/get-shit-done/references/model-profile-resolution.md

Resolve model for:
- `gsd-integration-checker`

## Step 1: Determine Milestone Scope

```bash
ls -d .planning/phases/*/ | sort -V
```

- Parse version from arguments or detect from ROADMAP.md
- Identify all phase directories in scope
- Extract milestone definition of done
- Extract requirements mapped to this milestone

## Step 2: Read All Phase Verifications

For each phase directory:
```bash
cat .planning/phases/01-*/*-VERIFICATION.md
cat .planning/phases/02-*/*-VERIFICATION.md
```

Extract from each:
- Status: passed | gaps_found
- Critical gaps (blockers)
- Non-critical gaps (tech debt, deferred)
- Anti-patterns (TODOs, stubs, placeholders)
- Requirements coverage

Flag unverified phases as blockers.

## Step 3: Spawn Integration Checker

```
Task(
  prompt="Check cross-phase integration and E2E flows.\n\nPhases: {phase_dirs}\nPhase exports: {from SUMMARYs}\nAPI routes: {routes created}\n\nVerify cross-phase wiring and E2E user flows.",
  subagent_type="gsd-integration-checker",
  model="{integration_checker_model}"
)
```

## Step 4: Collect Results

Combine:
- Phase-level gaps and tech debt
- Integration checker report (wiring gaps, broken flows)

## Step 5: Check Requirements Coverage

For each requirement:
- Find owning phase
- Check phase verification status
- Determine: satisfied | partial | unsatisfied

## Step 6: Write Audit Report

Create `.planning/v{version}-MILESTONE-AUDIT.md`:

```yaml
---
milestone: {version}
audited: {timestamp}
status: passed | gaps_found | tech_debt
scores:
  requirements: N/M
  phases: N/M
  integration: N/M
  flows: N/M
gaps:
  requirements: [...]
  integration: [...]
  flows: [...]
tech_debt:
  - phase: 01-auth
    items: [...]
---
```

## Step 7: Present Results

Route by status:

**If passed:**
```
## ✓ Milestone {version} — Audit Passed

/complete-milestone {version}
```

**If gaps_found:**
```
## ⚠ Milestone {version} — Gaps Found

/plan-milestone-gaps
```

**If tech_debt:**
```
## ⚡ Milestone {version} — Tech Debt Review

Options:
A. /complete-milestone — accept debt
B. /plan-milestone-gaps — address debt first
```
