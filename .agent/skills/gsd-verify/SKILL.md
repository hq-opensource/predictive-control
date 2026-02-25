---
name: gsd-verify
description: Validate built features through goal-backward analysis and UAT.
---
# GSD Verify Skill

This skill ensures that implemented features actually meet the project requirements and phase goals.

## 1. Goal-Backward Verification
Don't just check if tasks are done; check if the *goal* is achieved.
- **Truths**: Observable behaviors (e.g., "User can login").
- **Artifacts**: Physical files must exist and be substantive (not stubs).
- **Wiring**: Components must be correctly connected to APIs and Databases.

## 2. User Acceptance Testing (UAT)
Systematic testing with the human user.
- **Test cases**: Derived from the phase goals and requirements.
- **Gap tracking**: Issues reported by the user are logged as "Gaps" for diagnosis.
- **Inferred Severity**: Determine severity (blocker, major, cosmetic) based on user descriptions.

## 3. Verification Report
Create a `.planning/phases/XX-name/XX-VERIFICATION.md` report after execution.
- Summarize which "Must-Haves" passed or failed.
- List any "Anti-Patterns" (TODOs, stubs, hardcoded values).
- Provide recommended fix plans if gaps are found.

## 4. Subagents
Detailed agent definitions are located in `resources/agents/`:
- **verifier.md**: Verifies phase goal achievement.
- **integration-checker.md**: Verifies cross-phase integration and E2E flows.
