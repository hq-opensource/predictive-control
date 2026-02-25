---
description: Surface Agent's assumptions about a phase before planning.
---
## Purpose

Surface analysis of what the Agent thinks about a phase, enabling user to correct misconceptions early. No file output, purely conversational.

## Step 1: Validate Phase

Phase number required. Check `ROADMAP.md` for phase existence. Parse phase details.

## Step 2: Analyze Phase

Identify assumptions in:
1. **Technical Approach:** Libraries, frameworks, patterns.
2. **Implementation Order:** Sequencing of work.
3. **Scope Boundaries:** In-scope vs Out-of-scope.
4. **Risk Areas:** Complexity and challenges.
5. **Dependencies:** Internal and external requirements.

Mark assumptions with confidence levels (Confident, Assuming, Unclear).

## Step 3: Present Assumptions

Present in scannable format and ask the user for feedback:
"Are these assumptions accurate? What did I get right/wrong?"

## Step 4: Gather Feedback

- If corrections: Acknowledge and summarize new understanding.
- If confirmed: Assumptions validated.

## Step 5: Offer Next

1. /discuss-phase {PHASE} - Deep dive questions
2. /plan-phase {PHASE} - Create plans
3. Re-examine assumptions (apply corrections)
4. Done
