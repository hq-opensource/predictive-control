---
description: Execute discovery at the appropriate depth level. Produces DISCOVERY.md that informs PLAN.md creation.
---
## Depth Levels

| Level | Name         | Output                                       | When                                      |
| ----- | ------------ | -------------------------------------------- | ----------------------------------------- |
| 1     | Quick Verify | No file, proceed with verified knowledge     | Single library, confirming current syntax |
| 2     | Standard     | DISCOVERY.md                                 | Choosing between options, new integration |
| 3     | Deep Dive    | Detailed DISCOVERY.md with validation gates  | Architectural decisions, novel problems   |

## Source Hierarchy

**MANDATORY: Context7 BEFORE WebSearch**

1. **Context7 MCP FIRST** - Current docs, no hallucination
2. **Official docs** - When Context7 lacks coverage
3. **WebSearch LAST** - For comparisons and trends only

## Step 1: Determine Depth

Check the depth parameter:
- `depth=verify` → Level 1 (Quick Verification)
- `depth=standard` → Level 2 (Standard Discovery)
- `depth=deep` → Level 3 (Deep Dive)

## Level 1: Quick Verification

1. Resolve library in Context7.
2. Fetch relevant docs.
3. Verify current version and syntax.
4. **If verified:** Return with confirmation.
5. **If concerns found:** Escalate to Level 2.

## Level 2: Standard Discovery

1. Identify what to discover.
2. Context7 for each option.
3. Official docs for gaps.
4. WebSearch for comparisons.
5. Cross-verify results.
6. Create DISCOVERY.md.

## Level 3: Deep Dive

1. Scope the discovery.
2. Exhaustive Context7 research.
3. Official documentation deep read.
4. WebSearch for ecosystem context.
5. Cross-verify ALL findings.
6. Create comprehensive DISCOVERY.md.

## Final Steps (Level 2-3)

1. **Confidence Gate:** If confidence is LOW, ask user how to proceed.
2. **Open Questions Gate:** Present open questions to user.
3. **Offer Next:**
```
Discovery complete: .planning/phases/XX-name/DISCOVERY.md
---
## ▶ Next Up
1. /discuss-phase [current-phase]
2. /plan-phase [current-phase]
---
```
