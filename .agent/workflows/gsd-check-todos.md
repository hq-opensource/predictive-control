---
description: List pending todos, allow selection, load context, and route to action.
---
## Step 1: Check Existence

```bash
TODO_COUNT=$(ls .planning/todos/pending/*.md 2>/dev/null | wc -l | tr -d ' ')
```

If 0:
```
No pending todos.

Todos are captured during work sessions with /add-todo.

Would you like to:
1. Continue with current phase (/progress)
2. Add a todo now (/add-todo)
```
Exit.

## Step 2: Parse Filter

Check for area filter in arguments:
- `/check-todos` → show all
- `/check-todos api` → filter to area:api

## Step 3: List Todos

```bash
for file in .planning/todos/pending/*.md; do
  created=$(grep "^created:" "$file" | cut -d' ' -f2)
  title=$(grep "^title:" "$file" | cut -d':' -f2- | xargs)
  area=$(grep "^area:" "$file" | cut -d' ' -f2)
  echo "$created|$title|$area|$file"
done | sort
```

Display:
```
Pending Todos:

1. Add auth token refresh (api, 2d ago)
2. Fix modal z-index issue (ui, 1d ago)
3. Refactor database pool (database, 5h ago)

Reply with a number, or `q` to exit
```

## Step 4: Handle Selection

Wait for number. If invalid, reprompt.

## Step 5: Load Context

Read todo file. Display:
```
## [title]

**Area:** [area]
**Created:** [date]
**Files:** [list]

### Problem
[content]

### Solution
[content]
```

If files listed, summarize each.

## Step 6: Check Roadmap

If todo's area matches an upcoming phase, note for action options.

## Step 7: Offer Actions

**If matches roadmap phase:** - "Work on it now" - "Add to phase plan" - "Brainstorm approach" - "Put it back"

**If no match:** - "Work on it now" - "Create a phase" - "Brainstorm approach" - "Put it back"

## Step 8: Execute Action

**Work on it now:**
```bash
mv ".planning/todos/pending/[file]" ".planning/todos/done/"
```
Update STATE.md. Begin work.

**Add to phase plan / Create a phase / Brainstorm:** Keep in pending, route appropriately.

**Put it back:** Return to list.

## Step 9: Commit

@./.gemini/get-shit-done/references/git-planning-commit.md

If todo moved:
```bash
git add .planning/todos/done/[file]
git commit -m "docs: start work on todo - [title]"
```
