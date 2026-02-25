# Architecture Template
Template for `.planning/codebase/ARCHITECTURE.md` - captures conceptual code organization.

## File Template
```markdown
# Architecture

**Analysis Date:** [YYYY-MM-DD]

## Pattern Overview
**Overall:** [Pattern name: e.g., "Monolithic CLI", "Serverless API", "Full-stack MVC"]

**Key Characteristics:**
- [Characteristic 1]
- [Characteristic 2]

## Layers
**[Layer Name]:**
- Purpose: [What this layer does]
- Contains: [Types of code]
- Depends on: [What it uses]
- Used by: [What uses it]

## Data Flow
**[Flow Name]:**
1. [Entry point]
2. [Processing step]
3. [Output]

**State Management:**
- [How state is handled]

## Key Abstractions
**[Abstraction Name]:**
- Purpose: [What it represents]
- Examples: [e.g., "UserService"]
- Pattern: [e.g., "Singleton"]

## Entry Points
**[Entry Point]:**
- Location: [Path]
- Triggers: [What invokes it]
- Responsibilities: [What it does]

## Error Handling
**Strategy:** [Overall strategy]

## Cross-Cutting Concerns
**Logging:** [Approach]
**Validation:** [Approach]
**Authentication:** [Approach]
```
