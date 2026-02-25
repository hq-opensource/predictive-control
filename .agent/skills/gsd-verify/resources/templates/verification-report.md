# Verification Report Template
Template for `XX-VERIFICATION.md` — goal verification results.

## File Template
```markdown
---
phase: XX-name
verified: [timestamp]
status: passed | gaps_found
score: N/M must-haves
---

# Phase [X]: [Name] Verification Report

## Goal Achievement
### Observable Truths
| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | [truth] | ✓ VERIFIED | [proof] |

### Required Artifacts
| Artifact | Status | Details |
|----------|--------|---------|
| [path]   | ✓ EXISTS | [substance check] |

### Key Link Verification
| From | To | Status | Details |
|------|----|--------|---------|
| [A]  | [B] | ✓ WIRED | [link proof] |

## Anti-Patterns Found
| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| [path] | [TODO] | ⚠️ Warning | [desc] |

## Gaps Summary
### Critical Gaps
1. [Name]: [Fix]

## Recommended Fix Plans
### [phase]-[next]-PLAN.md: [Fix Name]
- [Task]
```
