---
name: gsd-core
description: Core principles and patterns for the Get Shit Done (GSD) framework. Includes questioning, TDD, verification patterns, and UI brand guidelines.
---

# GSD Core Skill

This skill provides the foundational knowledge and patterns for executing the Get Shit Done (GSD) framework.

## 1. Deep Questioning
Project initialization is dream extraction. Be a thinking partner, not an interviewer.
- **Start open**: Let the user dump their mental model.
- **Challenge vagueness**: Never accept fuzzy answers.
- **Make abstract concrete**: Ask for examples or walkthroughs.
- **Goal**: Enough clarity to write a `PROJECT.md` that downstream phases can act on.

## 2. Test Driven Development (TDD)
Use TDD for business logic, API endpoints, and data transformations.
- **Cycle**: RED (failing test) → GREEN (pass) → REFACTOR (cleanup).
- **Commit Pattern**: `test(XX-YY): add failing test`, `feat(XX-YY): implement feature`, `refactor(XX-YY): cleanup`.
- **Focus**: Design quality, not just coverage.

## 3. Verification Patterns
Existence ≠ Implementation. Check for:
- **Substantive**: Real code, not stubs (TODOs, hardcoded values).
- **Wired**: Proper imports and connections (Component → API → DB).
- **Functional**: Actually works as expected.

## 4. UI Brand Guidelines
Maintain a premium, consistent look for all GSD-related output.
- **Banners**: Use the `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━` style.
- **Checkpoints**: Use explicit boxes for user actions.
- **Next Up**: Always provide a clear instruction for the next step.

## 5. Git Strategy
Commit outcomes, not process.
- **Atomic**: One commit per task.
- **Metadata**: Unified commits for plan completion.
- **Handoffs**: WIP commits for session continuity.

## 6. Planning & State
The project's memory is stored in structured Markdown files in `.planning/`.
- **PROJECT.md**: The permanent context (Core Value, Requirements, Constraints).
- **ROADMAP.md**: The journey (Phases and Plans).
- **STATE.md**: The living memory (Current position, Performance metrics, Session continuity).
- **PLAN.md**: Executable tasks with automated/human checkpoints.
- **SUMMARY.md**: Results, decisions, and tech debt tracking for each plan.

## 7. Subagents
Detailed agent definitions are located in `resources/agents/`:
- **planner.md**: Creates executable phase plans.
- **plan-checker.md**: Verifies plan quality before execution.
- **roadmapper.md**: Creates project roadmaps and requirement mappings.
- **executor.md**: Executes plans and manages commits.
