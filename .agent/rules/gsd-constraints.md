# GSD System Constraints

This rule ensures that the GSD system maintains its structural integrity and follows specified constraints.

## Model Profiles
When spawning subagents within the GSD framework, always resolve the model profile from `.planning/config.json`.
- **Quality**: Opus for most agents, Sonnet for verification.
- **Balanced**: Opus for planning, Sonnet for execution/verification.
- **Budget**: Sonnet for writing, Haiku for research/verification.

## File Structure & Naming
Maintain the `.planning/` directory structure exactly:
- **Phases**: `.planning/phases/XX-name/` (zero-padded, lowercase-hyphenated).
- **Plans**: `.planning/phases/XX-name/XX-YY-PLAN.md`.
- **Summaries**: `.planning/phases/XX-name/XX-YY-SUMMARY.md`.
- **ROADMAP.md**: The primary source of phase status and requirement mapping.
- **STATE.md**: The project's persistent memory.

## Git Commits
Every task completion MUST result in a commit following the pattern:
`{type}({phase}-{plan}): {description}`
Example: `feat(01-01): create user login component`

## Checkpoints
Never skip checkpoints. If a task requires human verification or a decision, the orchestrator MUST stop and present the checkpoint using the GSD UI patterns.
