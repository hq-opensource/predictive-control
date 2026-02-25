# UAT Template
Template for `XX-UAT.md` — persistent UAT session tracking.

## File Template
```markdown
---
status: testing | complete | diagnosed
phase: XX-name
started: [timestamp]
---

## Current Test
number: [N]
name: [test name]
expected: [behavior]
awaiting: user response

## Tests
### 1. [Name]
expected: [behavior]
result: [pending / pass / issue]

## Summary
total: [N]
passed: [N]
issues: [N]

## Gaps
- truth: "[expected]"
  status: failed
  reason: "[user report]"
  severity: blocker | major | minor
```
