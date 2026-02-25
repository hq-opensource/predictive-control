# Debug Subagent Prompt
This prompt is used when spawning a `gsd-debugger` agent to investigate an issue.

## Prompt
```markdown
<objective>
Investigate issue: {issue_id}
**Summary:** {issue_summary}
</objective>

<symptoms>
expected: {expected}
actual: {actual}
errors: {errors}
reproduction: {reproduction}
timeline: {timeline}
</symptoms>

<debug_file>
Create: .planning/debug/{slug}.md
</debug_file>
```
