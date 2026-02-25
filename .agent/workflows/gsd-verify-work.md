---
description: Validate built features through conversational testing with the user.
---
## Philosophy: User tests, Agent records.

Present what SHOULD happen, ask if it does. "yes/n/next" = pass. Anything else = issue.

## Step 1: Check Active Session

Check for existing `*-UAT.md` files.
- If sessions exist: Offer to resume.
- If new: Proceed to extraction.

## Step 2: Extract Tests

Find the phase directory and `SUMMARY.md` files. Extract user-facing deliverables (features, UI changes). Create a test for each:
- **Test:** Name of the interaction.
- **Expected:** Specific observable behavior.

## Step 3: Create UAT File

Create `{phase}-UAT.md` with:
- Frontmatter (status, phase).
- Current Test tracker.
- Full checklist of pending tests.
- Summary & Gaps sections.

## Step 4: Iterative Testing

For each test:
1. Present "CHECKPOINT: Verification Required".
2. Describe what should happen.
3. Wait for user response.
4. If success: Mark pass.
5. If failure: Record user response, infer severity (blocker, major, minor, cosmetic). Add to "Gaps" section.

## Step 5: Diagnose & Plan Fixes

When all tests are done (or interrupted):
1. **Diagnose:** Spawn parallel debug agents for each issue in Gaps.
2. **Plan:** Spawn planner in `--gaps` mode to create fix plans.
3. **Verify:** Spawn plan checker to validate fix plans.
4. **Iterate:** Revision loop until fix plans are solid.

## Step 6: Completion

Commit the UAT file and present next steps (execute fixes if any, or next phase).
