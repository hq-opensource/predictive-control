# Architecture Research Template
Template for `.planning/research/ARCHITECTURE.md` — system structure patterns.

## File Template
```markdown
# Architecture Research

**Domain:** [domain type]
**Researched:** [date]
**Confidence:** [HIGH/MEDIUM/LOW]

## Standard Architecture
### System Overview
[Overview of major layers/components]

### Component Responsibilities
| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| [name]    | [what it owns] | [how it's built]       |

## Recommended Project Structure
```
src/
├── [folder]/           # [purpose]
└── [file].ts           # [purpose]
```

## Architectural Patterns
### [Pattern Name]
- What: [description]
- When to use: [conditions]
- Trade-offs: [pros/cons]

## Data Flow
### Request Flow
[User Action] → [Handler] → [Service] → [Data Store]

## Scaling Considerations
[Bottlenecks and scaling path]

## Anti-Patterns
[Common mistakes to avoid]

## Integration Points
[External services and internal boundaries]
```
