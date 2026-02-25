---
description: Capture idea or task as todo from current conversation context.
---
## Step 1: Ensure Structure

`mkdir -p .planning/todos/pending .planning/todos/done`

## Step 2: Extract Content

- **With Arguments:** Use as title (e.g., `/add-todo Add auth token refresh`).
- **Without Arguments:** Analyze recent conversation for features, problems, code paths, or errors mentioned.

## Step 3: Infer Area

Map files/paths to areas (e.g., `src/api` -> `api`, `src/ui` -> `ui`, `src/db` -> `database`).

## Step 4: Check Duplicates

Grep existing todos in `.planning/todos/pending/` to avoid overlaps.

## Step 5: Create Todo

Write to `.planning/todos/pending/{YYYY-MM-DD}-{slug}.md`:
- Title
- Area
- Referenced Files
- Problem description (full context)
- Solution hints (if any)

## Step 6: Update State & Commit

Update `STATE.md` count. Commit the new todo to git.
