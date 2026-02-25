---
name: gsd-mapping
description: Instructions and templates for mapping an existing codebase to understand its architecture, stack, and conventions.
---

# GSD Mapping Skill

Use this skill when you need to understand an existing codebase to plan or execute changes.

## 1. Mapping Objects
A full codebase map consists of the following documents in `.planning/codebase/`:
1. **ARCHITECTURE.md**: Conceptual layers and data flow.
2. **STACK.md**: Languages, frameworks, and critical dependencies.
3. **STRUCTURE.md**: Physical file organization and directory purposes.
4. **CONVENTIONS.md**: Coding style, naming patterns, and error handling.
5. **TESTING.md**: Test frameworks, runners, and mocking patterns.
6. **INTEGRATIONS.md**: External services and APIs.
7. **CONCERNS.md**: Tech debt, known bugs, and fragile areas.

## 2. How to Map
1. **Start with Entry Points**: Identify where the app starts (e.g., `index.ts`, `main.py`, `server.js`).
2. **Trace Imports**: Follow imports to identify layers (Services, Controllers, Utils).
3. **Check Config Files**: Look at `package.json`, `tsconfig.json`, `.eslintrc`, etc., to identify the stack and conventions.
4. **Scan for Patterns**: Look at 5-10 files to identify naming and style consistency.

## 3. Resources
Templates for these documents are located in `resources/templates/`.

## 4. Subagents
Detailed agent definitions are located in `resources/agents/`:
- **codebase-mapper.md**: Explores codebase and writes analysis docs.
