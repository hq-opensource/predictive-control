---
name: gsd-best-practices
description: Best practices for agentic workflow coordination, checkpoints, and session continuity.
---

# GSD Best Practices Skill

This skill provides refined patterns for coordinating complex agentic workflows, handling user interaction points (checkpoints), and maintaining session continuity.

## 1. Interaction Points (Checkpoints)
GSD uses structured checkpoints to formalize interaction with the user.
- **Human-Verify**: Used when code is written/deployed. Claude sets up the environment (e.g., starts dev server) and the user confirms visual/functional behavior.
- **Decision**: Used when architectural or technology choices are needed. Claude presents balanced pros/cons.
- **Human-Action**: Used ONLY for non-automatable steps like email verification or MFA.

**Golden Rule**: If it has a CLI or API, the agent must automate it. Never ask a user to run a command that the agent can execute.

## 2. Session Continuity
Always provide a clear "Next Up" block after completing a major task.
- **Format**: Give the name, description, and the exact command to copy-paste.
- **Context**: Pull names from `ROADMAP.md` or `PLAN.md`.
- **Advice**: Always suggest `/clear` before starting a new phase/plan to keep the context window fresh.

## 3. Planning Configuration
Configuration for the `.planning/` directory should be respected:
- `commit_docs`: If true (default), commit planning artifacts to git. If false, keep them local.
- `search_gitignored`: If true, include `.planning/` in broad searches even if gitignored.
- `git.branching_strategy`: Support `none`, `phase`, or `milestone` branching.

## 4. Execution Protocol
- **Stop at Checkpoints**: Do not proceed until the user responds.
- **Verify Setup**: Never ask a user to visit a URL if the server failed to start or the deployment failed. Fix the environment first.
- **Atomic Commits**: Each task in a plan should result in an atomic commit once it's verified.
