---
name: gsd-research
description: Instructions and templates for researching implementation approaches for new projects or phases.
---

# GSD Research Skill

Use this skill when researching how to implement a new feature, project, or phase.

## 1. Research Objects
Research produces the following documents in `.planning/research/`:
1. **SUMMARY.md**: Executive summary and roadmap implications.
2. **STACK.md**: Recommended technologies and versions.
3. **FEATURES.md**: Table stakes, differentiators, and MVP definition.
4. **ARCHITECTURE.md**: Recommended system structure and patterns.
5. **PITFALLS.md**: Common mistakes and technical debt to avoid.

## 2. How to Research
1. **Understand Domain**: Identify the core problem and industry standards.
2. **Identify Table Stakes**: Determine what users expect as "default".
3. **Select Stack**: Recommend technologies based on project requirements and team expertise.
4. **Predict Pitfalls**: Look for common failure modes in similar implementations.
5. **Map to Roadmap**: Translate findings into actionable phases.

## 3. Resources
Templates for these documents are located in `resources/templates/`.

## 4. Subagents
Detailed agent definitions are located in `resources/agents/`:
- **phase-researcher.md**: Researches implementation details for a phase.
- **project-researcher.md**: Researches domain ecosystems for new projects.
- **research-synthesizer.md**: Consolidates parallel research into a summary.
