---
description: Add a new integer phase to the end of the current milestone.
---
## Step 1: Parse Arguments

All arguments become the description.

```
ERROR: Phase description required
Usage: /add-phase <description>
```

## Step 2: Load Roadmap

```bash
cat .planning/ROADMAP.md
```

Error if not found.

## Step 3: Find Current Milestone

Locate `## Current Milestone:` heading.
Identify all phases in this milestone.

## Step 4: Calculate Next Phase

Find highest integer phase, add 1.
Format as two-digit: `printf "%02d" $next`

## Step 5: Generate Slug

```bash
slug=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
```

## Step 6: Create Directory

```bash
mkdir -p ".planning/phases/${phase_num}-${slug}"
```

## Step 7: Update ROADMAP.md

Insert at end of milestone:

```markdown
### Phase {N}: {Description}

**Goal:** [To be planned]
**Depends on:** Phase {N-1}
**Plans:** 0 plans
```

## Step 8: Update STATE.md

Add to "Roadmap Evolution":
```
- Phase {N} added: {description}
```

## Step 9: Completion

```
Phase {N} added to current milestone:
- Directory: .planning/phases/{NN}-{slug}/
- Status: Not planned yet

---

## ▶ Next Up

/plan-phase {N}

---

**Also available:**
- /add-phase <description> — add another
```
