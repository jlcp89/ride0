# Context Assembly Guide — Feature Scoping

> Great specs come from great context. Automate the obvious, ask about the unknowable.

This framework feeds into **spec generation**. Context assembly gathers what's needed to write a precise SPEC.md, combining automated codebase analysis with targeted questions.

## Layer 1 — Codebase Research (automated)

Before asking the user anything, use an Explore agent to gather:

| Signal | What to Look For | Maps to Spec Section |
|--------|-------------------|---------------------|
| Similar features | Where do comparable features live? What patterns do they follow? | Changes (file selection) |
| Existing APIs | What interfaces, types, and contracts already exist? | Changes (constraints) |
| Test patterns | How are similar features tested? What test utilities exist? | Test Plan |
| Architecture | What's the module boundary? Where does this feature fit? | Changes (ordering) |

Produces a **Feature Context** with what's known and what's still uncertain.

## Layer 2 — Complexity Classification (automatic)

| Level | Criteria | Question Budget |
|-------|----------|-----------------|
| **trivial** | 1-3 files, follows existing pattern exactly | 1 question (just gotchas) |
| **standard** | 4-10 files, some new patterns needed | 2-3 questions |
| **complex** | 10+ files, new patterns, cross-cutting concerns | 3-4 questions |

## Layer 3 — Targeted Questions

Present the Feature Context first, then ask only what can't be inferred. Pick from this pool based on complexity:

**Always ask (all levels):**

> **Gotchas**: What edge cases, error scenarios, or constraints should we handle? What "obvious" approach doesn't work here?

**Ask for standard+ complexity:**

> **Acceptance**: How will we know this feature is complete? What are the acceptance criteria?

> **Constraints**: Are there technical constraints, design decisions, or patterns we must follow?

**Ask for complex features:**

> **Risks**: What parts are most uncertain or risky? What assumptions might be wrong?

## Context → Spec Mapping

| Context Source | Spec Section |
|---------------|-------------|
| Feature description | Problem |
| Layer 1 research + constraints answer | Solution, Changes |
| Acceptance answer | Verification |
| Gotchas answer | Test Plan (edge cases) |
| Layer 1 architecture analysis | Changes (ordering) |
