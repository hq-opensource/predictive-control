---
description: Mark a shipped version (v1.0, v1.1, v2.0) as complete.
---
## Required Reading

**Read these files NOW:**

1. templates/milestone.md
2. templates/milestone-archive.md
3. `.planning/ROADMAP.md`
4. `.planning/REQUIREMENTS.md`
5. `.planning/PROJECT.md`

## Archival Behavior

When a milestone completes, this workflow:

1. Extracts full milestone details to `.planning/milestones/v[X.Y]-ROADMAP.md`
2. Archives requirements to `.planning/milestones/v[X.Y]-REQUIREMENTS.md`
3. Updates ROADMAP.md to replace milestone details with one-line summary
4. Deletes REQUIREMENTS.md (fresh one created for next milestone)
5. Performs full PROJECT.md evolution review
6. Offers to create next milestone inline

**Context Efficiency:** Archives keep ROADMAP.md constant-size and REQUIREMENTS.md milestone-scoped.

**Archive Format:**

**ROADMAP archive** uses `templates/milestone-archive.md` template with:
- Milestone header (status, phases, date)
- Full phase details from roadmap
- Milestone summary (decisions, issues, technical debt)

**REQUIREMENTS archive** contains:
- All v1 requirements marked complete with outcomes
- Traceability table with final status
- Notes on any requirements that changed during milestone

## Step 1: Verify Readiness

Check if milestone is truly complete:

```bash
cat .planning/ROADMAP.md
ls .planning/phases/*/SUMMARY.md 2>/dev/null | wc -l
```

**Questions to ask:**

- Which phases belong to this milestone?
- Are all those phases complete (all plans have summaries)?
- Has the work been tested/validated?
- Is this ready to ship/tag?

Present:

```
Milestone: [Name from user, e.g., "v1.0 MVP"]

Appears to include:
- Phase 1: Foundation (2/2 plans complete)
- Phase 2: Authentication (2/2 plans complete)
- Phase 3: Core Features (3/3 plans complete)
- Phase 4: Polish (1/1 plan complete)

Total: 4 phases, 8 plans, all complete
```

**Config Check:**

```bash
cat .planning/config.json 2>/dev/null
```

**If mode="yolo":**

```
⚡ Auto-approved: Milestone scope verification

[Show breakdown summary without prompting]

Proceeding to stats gathering...
```

Proceed directly to gather_stats step.

**If mode="interactive" OR="custom with gates.confirm_milestone_scope true":**

```
Ready to mark this milestone as shipped?
(yes / wait / adjust scope)
```

Wait for confirmation.

If "adjust scope": Ask which phases should be included.
If "wait": Stop, user will return when ready.

## Step 2: Gather Stats

Calculate milestone statistics:

```bash
# Count phases and plans in milestone
# (user specified or detected from roadmap)

# Find git range
git log --oneline --grep="feat(" | head -20

# Count files modified in range
git diff --stat FIRST_COMMIT..LAST_COMMIT | tail -1

# Count LOC (adapt to language)
find . -name "*.swift" -o -name "*.ts" -o -name "*.py" | xargs wc -l 2>/dev/null

# Calculate timeline
git log --format="%ai" FIRST_COMMIT | tail -1  # Start date
git log --format="%ai" LAST_COMMIT | head -1   # End date
```

Present summary:

```
Milestone Stats:
- Phases: [X-Y]
- Plans: [Z] total
- Tasks: [N] total (estimated from phase summaries)
- Files modified: [M]
- Lines of code: [LOC] [language]
- Timeline: [Days] days ([Start] → [End])
- Git range: feat(XX-XX) → feat(YY-YY)
```

## Step 3: Extract Accomplishments

Read all phase SUMMARY.md files in milestone range:

```bash
cat .planning/phases/01-*/01-*-SUMMARY.md
cat .planning/phases/02-*/02-*-SUMMARY.md
# ... for each phase in milestone
```

From summaries, extract 4-6 key accomplishments.

Present:

```
Key accomplishments for this milestone:
1. [Achievement from phase 1]
2. [Achievement from phase 2]
3. [Achievement from phase 3]
4. [Achievement from phase 4]
5. [Achievement from phase 5]
```

## Step 4: Create Milestone Entry

Create or update `.planning/MILESTONES.md`.

If file doesn't exist:

```markdown
# Project Milestones: [Project Name from PROJECT.md]

[New entry]
```

If exists, prepend new entry (reverse chronological order).

Use template from `templates/milestone.md`:

```markdown
## v[Version] [Name] (Shipped: YYYY-MM-DD)

**Delivered:** [One sentence from user]

**Phases completed:** [X-Y] ([Z] plans total)

**Key accomplishments:**

- [List from previous step]

**Stats:**

- [Files] files created/modified
- [LOC] lines of [language]
- [Phases] phases, [Plans] plans, [Tasks] tasks
- [Days] days from [start milestone or start project] to ship

**Git range:** `feat(XX-XX)` → `feat(YY-YY)`

**What's next:** [Ask user: what's the next goal?]

---
```

## Step 5: Evolve Project Full Review

Perform full PROJECT.md evolution review at milestone completion.

**Read all phase summaries in this milestone:**

```bash
cat .planning/phases/*-*/*-SUMMARY.md
```

**Full review checklist:**

1. **"What This Is" accuracy:**
   - Read current description
   - Compare to what was actually built
   - Update if the product has meaningfully changed

2. **Core Value check:**
   - Is the stated core value still the right priority?
   - Did shipping reveal a different core value?
   - Update if the ONE thing has shifted

3. **Requirements audit:**

   **Validated section:**
   - All Active requirements shipped in this milestone → Move to Validated
   - Format: `- ✓ [Requirement] — v[X.Y]`

   **Active section:**
   - Remove requirements that moved to Validated
   - Add any new requirements for next milestone
   - Keep requirements that weren't addressed yet

   **Out of Scope audit:**
   - Review each item — is the reasoning still valid?
   - Remove items that are no longer relevant
   - Add any requirements invalidated during this milestone

4. **Context update:**
   - Current codebase state (LOC, tech stack)
   - User feedback themes (if any)
   - Known issues or technical debt to address

5. **Key Decisions audit:**
   - Extract all decisions from milestone phase summaries
   - Add to Key Decisions table with outcomes where known
   - Mark ✓ Good, ⚠️ Revisit, or — Pending for each

6. **Constraints check:**
   - Any constraints that changed during development?
   - Update as needed

**Update PROJECT.md:**

Make all edits inline. Update "Last updated" footer:

```markdown
---
*Last updated: [date] after v[X.Y] milestone*
```

**Step complete when:**

- [ ] "What This Is" reviewed and updated if needed
- [ ] Core Value verified as still correct
- [ ] All shipped requirements moved to Validated
- [ ] New requirements added to Active for next milestone
- [ ] Out of Scope reasoning audited
- [ ] Context updated with current state
- [ ] All milestone decisions added to Key Decisions
- [ ] "Last updated" footer reflects milestone completion

## Step 6: Reorganize Roadmap

Update `.planning/ROADMAP.md` to group completed milestone phases.

Add milestone headers and collapse completed work:

```markdown
# Roadmap: [Project Name]

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped YYYY-MM-DD)
- 🚧 **v1.1 Security** — Phases 5-6 (in progress)
- 📋 **v2.0 Redesign** — Phases 7-10 (planned)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED YYYY-MM-DD</summary>

- [x] Phase 1: Foundation (2/2 plans) — completed YYYY-MM-DD
- [x] Phase 2: Authentication (2/2 plans) — completed YYYY-MM-DD
- [x] Phase 3: Core Features (3/3 plans) — completed YYYY-MM-DD
- [x] Phase 4: Polish (1/1 plan) — completed YYYY-MM-DD

</details>

### 🚧 v[Next] [Name] (In Progress / Planned)

- [ ] Phase 5: [Name] ([N] plans)
- [ ] Phase 6: [Name] ([N] plans)

## Progress

| Phase             | Milestone | Plans Complete | Status      | Completed  |
| ----------------- | --------- | -------------- | ----------- | ---------- |
| 1. Foundation     | v1.0      | 2/2            | Complete    | YYYY-MM-DD |
| 2. Authentication | v1.0      | 2/2            | Complete    | YYYY-MM-DD |
| 3. Core Features  | v1.0      | 3/3            | Complete    | YYYY-MM-DD |
| 4. Polish         | v1.0      | 1/1            | Complete    | YYYY-MM-DD |
| 5. Security Audit | v1.1      | 0/1            | Not started | -          |
| 6. Hardening      | v1.1      | 0/2            | Not started | -          |
```

## Step 7: Archive Milestone

Extract completed milestone details and create archive file.

**Process:**

1. Create archive file path: `.planning/milestones/v[X.Y]-ROADMAP.md`

2. Read `./.gemini/get-shit-done/templates/milestone-archive.md` template

3. Extract data from current ROADMAP.md:
   - All phases belonging to this milestone (by phase number range)
   - Full phase details (goals, plans, dependencies, status)
   - Phase plan lists with completion checkmarks

4. Extract data from PROJECT.md:
   - Key decisions made during this milestone
   - Requirements that were validated

5. Fill template {{PLACEHOLDERS}}

6. Write filled template to `.planning/milestones/v[X.Y]-ROADMAP.md`

7. Delete ROADMAP.md (fresh one created for next milestone):
   ```bash
   rm .planning/ROADMAP.md
   ```

8. Verify archive exists:
   ```bash
   ls .planning/milestones/v[X.Y]-ROADMAP.md
   ```

9. Confirm roadmap archive complete:

   ```
   ✅ v[X.Y] roadmap archived to milestones/v[X.Y]-ROADMAP.md
   ✅ ROADMAP.md deleted (fresh one for next milestone)
   ```

**Note:** Phase directories (`.planning/phases/`) are NOT deleted.

## Step 8: Archive Requirements

Archive requirements and prepare for fresh requirements in next milestone.

**Process:**

1. Read current REQUIREMENTS.md:
   ```bash
   cat .planning/REQUIREMENTS.md
   ```

2. Create archive file: `.planning/milestones/v[X.Y]-REQUIREMENTS.md`

3. Transform requirements for archive:
   - Mark all v1 requirements as `[x]` complete
   - Add outcome notes where relevant
   - Update traceability table status to "Complete"
   - Add "Milestone Summary" section

4. Write archive file with header

5. Delete original REQUIREMENTS.md:
   ```bash
   rm .planning/REQUIREMENTS.md
   ```

6. Confirm:
   ```
   ✅ Requirements archived to milestones/v[X.Y]-REQUIREMENTS.md
   ✅ REQUIREMENTS.md deleted (fresh one needed for next milestone)
   ```

## Step 9: Archive Audit

Move the milestone audit file to the archive (if it exists):

```bash
# Move audit to milestones folder (if exists)
[ -f .planning/v[X.Y]-MILESTONE-AUDIT.md ] && mv .planning/v[X.Y]-MILESTONE-AUDIT.md .planning/milestones/
```

Confirm:
```
✅ Audit archived to milestones/v[X.Y]-MILESTONE-AUDIT.md
```

## Step 10: Update State

Update STATE.md to reflect milestone completion.

**Project Reference:**

```markdown
## Project Reference

See: .planning/PROJECT.md (updated [today])

**Core value:** [Current core value from PROJECT.md]
**Current focus:** [Next milestone or "Planning next milestone"]
```

**Current Position:**

```markdown
Phase: [Next phase] of [Total] ([Phase name])
Plan: Not started
Status: Ready to plan
Last activity: [today] — v[X.Y] milestone complete

Progress: [updated progress bar]
```

## Step 11: Handle Branches

Check if branching was used and offer merge options.

```bash
# Get branching strategy from config
```

**If strategy is "none":** Skip to git_tag step.

**For "phase" strategy — find phase branches:**

**For "milestone" strategy — find milestone branch:**

**If no branches found:** Skip to git_tag step.

**If branches exist — present merge options:** Use AskUserQuestion to handle merge/delete/keep.

## Step 12: Git Tag

Create git tag for milestone:

```bash
git tag -a v[X.Y] -m "v[X.Y] completion details"
```

Confirm: "Tagged: v[X.Y]"

Ask: "Push tag to remote? (y/n)"

If yes:
```bash
git push origin v[X.Y]
```

## Step 13: Git Commit Milestone

Commit milestone completion including archive files and deletions.

```bash
# Stage archive files (new)
git add .planning/milestones/v[X.Y]-ROADMAP.md
git add .planning/milestones/v[X.Y]-REQUIREMENTS.md
git add .planning/milestones/v[X.Y]-MILESTONE-AUDIT.md 2>/dev/null || true

# Stage updated files
git add .planning/MILESTONES.md
git add .planning/PROJECT.md
git add .planning/STATE.md

# Stage deletions
git add -u .planning/

# Commit with descriptive message
git commit -m "chore: complete v[X.Y] milestone"
```

Confirm: "Committed: chore: complete v[X.Y] milestone"

## Step 14: Offer Next

```
✅ Milestone v[X.Y] [Name] complete

---
## ▶ Next Up
/new-milestone
---
```
