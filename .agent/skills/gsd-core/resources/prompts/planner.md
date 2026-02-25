# Planner Subagent Prompt
This prompt is used when spawning a `gsd-planner` agent to create plans for a phase.

## Prompt
```markdown
<planning_context>

**Phase:** {phase_number}
**Mode:** {standard | gap_closure}

**Project State:** @.planning/STATE.md
**Roadmap:** @.planning/ROADMAP.md
**Requirements:** @.planning/REQUIREMENTS.md
**Phase Context:** @.planning/phases/{phase_dir}/{phase}-CONTEXT.md
**Research:** @.planning/phases/{phase_dir}/{phase}-RESEARCH.md

</planning_context>

<downstream_consumer>
Output consumed by /gsd:execute-phase. Plans must be executable prompts with XML tasks and must_haves.
</downstream_consumer>
```
