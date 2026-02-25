# Debug Template
Template for `.planning/debug/[slug].md` — active debug session tracking.

## File Template
```markdown
---
status: gathering | investigating | fixing | verifying | resolved
trigger: "[user input]"
created: [timestamp]
updated: [timestamp]
---

## Current Focus
hypothesis: [current theory]
test: [how testing]
expecting: [threshold for success]
next_action: [immediate step]

## Symptoms
expected: [ideal]
actual: [reality]
errors: [logs]
reproduction: [steps]

## Eliminated
- hypothesis: [failed theory]
  evidence: [proof]

## Evidence
- checked: [file/log]
  found: [fact]
  implication: [meaning]

## Resolution
root_cause: [found]
fix: [applied]
verification: [confirmed]
```
