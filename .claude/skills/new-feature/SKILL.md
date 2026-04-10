---
name: new-feature
description: Implements a new feature using spec-driven workflow. Generates a structured spec for approval before writing any code. Assembles context from codebase research and targeted questions, produces SPEC.md, then implements after review. Use for any non-trivial feature.
---

# /new-feature — Spec-Driven Feature Implementation

Spec-first feature implementation. Generates a structured spec for approval before writing any code. Uses context assembly from [context-assembly-guide.md](context-assembly-guide.md) to feed spec generation.

> "The spec IS the engineering. The AI just types fast."

## Arguments

- Feature description (required) — What to build, in plain language

## Phase 1 — Spec Generation

### Step 1: Capture Feature Request

If `$ARGUMENTS` is provided, use it as the feature description.
Otherwise ask:

> "What feature are we building? Describe it in a sentence or two."

### Step 2: Research the Codebase

Use an Explore agent to understand:
- Where similar features live
- What patterns to follow
- What APIs/interfaces already exist
- What tests look like for similar features

### Step 3: Context Assembly

Assemble context using the layered approach from [context-assembly-guide.md](context-assembly-guide.md):

**Layer 1 — Automated** (already done in Step 2): Present what was found in the codebase.

**Layer 2 — Classify complexity**:
- **trivial** (1-3 files, existing pattern) → 1 question
- **standard** (4-10 files, some new patterns needed) → 2-3 questions
- **complex** (10+ files, new patterns) → 3-4 questions

**Layer 3 — Targeted questions** (only what can't be inferred):

Always ask:
> "What edge cases, error scenarios, or constraints should we handle? What 'obvious' approach doesn't work here?"

For standard+ complexity, also ask:
> "How will we know this feature is complete? What are the acceptance criteria?"

### Step 4: Generate Spec

Write `SPEC.md` in the project root:

```markdown
# Feature Spec: {feature_name}

## Problem
What user problem does this solve? (1-2 sentences)

## Solution
How will we solve it? (1-2 sentences synthesized from context)

## Changes

### File: {path}
- What changes and why

### New File: {path}
- Purpose and key contents

## API Changes
- New endpoints, parameters, or return types (if applicable)

## Test Plan
- [ ] Unit tests for {specific behavior}
- [ ] Integration test for {specific flow}
- [ ] Edge cases: {list from gotchas answer}

## Verification
1. Run: {command}
2. Check: {expected output}
3. Confirm: {user-visible behavior}
```

### Step 5: Present Spec for Approval

Show the spec and ask:

> "Does this spec match what you want? Any changes before I start implementing?"

Wait for approval. If user requests changes, update SPEC.md and re-present.

**HARD RULE**: You MUST NOT create, modify, or suggest code until the user explicitly approves the spec. No "let me start while we finalize." No code until approval.

## Phase 2 — Implementation

Only after explicit spec approval:

1. **Create branch** — `git checkout -b feature/{feature_name}`
2. **Implement changes** — Follow the spec's Changes section file by file
3. **Write tests** — Follow the spec's Test Plan
4. **Run verification** — Follow the spec's Verification section
5. **Commit** — One commit per logical change, referencing the spec

### Implementation Loop

For each file in the Changes section:
1. Make the changes described
2. Run the proof cycle (lint → test) after each file
3. If verification fails, fix before moving to the next file

## Phase 3 — Cleanup

1. **Delete SPEC.md** — Or move to `docs/specs/` if the team wants to keep specs
2. **Create requirements entry** — Add to `REQUIREMENTS.md`
3. **Update HANDOFF.md** — Record the feature implementation in next `/wrap`

## Related Skills
- `/reviewing-code` — review the implementation
