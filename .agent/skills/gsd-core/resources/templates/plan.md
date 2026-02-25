# Plan Template
Template for `.planning/phases/XX-name/XX-YY-PLAN.md` — executable plans.

## File Template
```markdown
---
phase: XX-name
plan: YY
type: execute
wave: N
depends_on: []
files_modified: []
autonomous: true
must_haves:
  truths: []
  artifacts: []
  key_links: []
---

<objective>
[What this plan accomplishes]
</objective>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
</context>

<tasks>
<task type="auto">
  <name>Task 1: [Name]</name>
  <files>[path]</files>
  <action>[Implementation details]</action>
  <verify>[Command]</verify>
  <done>[Criteria]</done>
</task>
</tasks>

<verification>
- [ ] [Check]
</verification>

<success_criteria>
- All tasks completed
</success_criteria>

<output>
After completion, create `{phase}-{plan}-SUMMARY.md`
</output>
```
