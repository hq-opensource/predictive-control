# 🚀 Get Shit Done (GSD) for Antigravity

This is a port of the **Get Shit Done** framework, optimized for the Antigravity agent. It replaces vague "vibecoding" with a rigorous, context-engineered workflow that ensures consistent, high-quality output without technical debt.

## 🧠 The Philosophy

GSD works by preventing **context rot**. As long-running sessions accumulate garbage, AI quality degrades. GSD solves this by:
1.  **Context Engineering**: Extracting everything into a persistent `.planning/` directory.
2.  **Vertical Slices (Phases)**: Building features end-to-end (Model → API → UI) in isolated bursts.
3.  **Atomic Commits**: Committing every single task outcome immediately.
4.  **Goal-Backward Verification**: Checking if the code actually works before completing a phase.

---

## 🛠️ Core Commands

Use these slash commands to drive your project from idea to ship.

### 1. Project Initialization
*   `/gsd-new-project` - **Greenfield**: For starting something from scratch. It will extract your vision, research the domain, and build a `ROADMAP.md`.
*   `/gsd-map-codebase` - **Brownfield**: For existing projects. It analyzes your stack, architecture, and tech debt first so future work respects your patterns.

### 2. Implementation Cycle (Repeat per Phase)
*   `/gsd-discuss-phase [N]` - **Extraction**: Shape the implementation. Discuss visual styles, API design, or edge cases before planning. Creates `CONTEXT.md`.
*   `/gsd-plan-phase [N]` - **Simulation**: Research the ecosystem and create atomic `PLAN.md` files with XML tasks.
*   `/gsd-execute-phase [N]` - **Construction**: Executes the plans in parallel waves. Commits outcomes automatically. No context spillover.
*   `/gsd-verify-work [N]` - **UAT**: Walks you through the deliverables. If a feature fails, it automatically diagnoses and creates fix plans.

### 3. Management & Utilities
*   `/gsd-progress` - View your project status and what's remaining.
*   `/gsd-quick` - For small bug fixes or tweaks that don't need a full phase.
*   `/gsd-complete-milestone` - Archive your work, tag the release, and prepare for the next version.
*   `/gsd-debug [issue]` - Systematic interactive debugging with a persistent "debug brain" in `.planning/debug/`.

---

## 📂 The `.planning/` Directory

GSD stores its "memory" here to keep the main context window light and fast:
*   `PROJECT.md`: Your vision, core value, and validated requirements.
*   `ROADMAP.md`: The sequence of phases (1, 2, 3...) and their status.
*   `STATE.md`: Short-term memory (Where we are, what happened last, current velocity).
*   `REQUIREMENTS.md`: The "Definition of Done" for the current milestone.

---

## 🏗️ Skills Integrated
The agent has been trained on specialized GSD skills:
*   `gsd-core`: TDD patterns, verification logic, and UI brand guidelines.
*   `gsd-git`: Outcome-based commit rules.
*   `gsd-mapping`: Expertise in analyzing complex codebases.
*   `gsd-research`: Deep-search methodology for unfamiliar tech stacks.

---
*"If you know clearly what you want, this WILL build it for you. No bs."*
