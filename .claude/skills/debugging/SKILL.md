---
name: debugging
description: Structured debugging workflow for errors, test failures, and unexpected behavior. Follows reproduce-hypothesize-isolate-fix-verify methodology with regression test. Use when encountering any bug or unexpected behavior.
---

# Debugging — Structured Workflow

Systematic approach to finding and fixing bugs. Follows: Understand → Reproduce → Hypothesize → Isolate → Fix → Verify → Prevent.

## Workflow

### Step 1: Understand the Bug

If `$ARGUMENTS` describes the bug, use it. Otherwise ask:

> "Describe the bug: what's happening vs. what should happen?"

Gather:
- **Actual behavior**: What happens now?
- **Expected behavior**: What should happen?
- **Reproduction steps**: How to trigger it?
- **Frequency**: Always, sometimes, only under conditions?
- **Error messages**: Exact text, stack traces

### Step 2: Reproduce

Before trying to fix anything, reproduce the bug:

1. Write a failing test that demonstrates the bug
2. Or run the exact reproduction steps and confirm the behavior
3. If you can't reproduce it, gather more information before proceeding

> "I'll write a test that demonstrates this bug first."

**Important**: If you cannot reproduce, STOP and report back. Do not guess at fixes.

**GATE 2**: Cannot proceed unless a failing test exists OR reproduction output is confirmed.

### Step 3: Hypothesize

Based on the reproduction, form hypotheses:

1. Read the relevant code paths
2. Trace the execution flow from input to unexpected output
3. List 2-3 possible root causes, ordered by likelihood
4. For each hypothesis, identify what evidence would confirm or deny it

> "My top hypotheses are:"
> 1. {hypothesis} — I'll check this by {evidence}
> 2. {hypothesis} — I'll check this by {evidence}

### Step 4: Isolate

Narrow down to the root cause:

1. Add targeted logging or breakpoints
2. Test each hypothesis with minimal changes
3. Binary search through code if the bug path is long
4. Check recent changes (`git log`, `git diff`) for related modifications

When root cause is found:
> "Root cause: {description}. It happens because {explanation}."

**GATE 3**: Cannot proceed unless root cause is identified with evidence.

### Step 5: Fix

Implement the minimal fix:

1. Change only what's necessary to fix the bug
2. Don't refactor surrounding code in the same change
3. Don't fix "related" issues — file them separately
4. Ensure the failing test from Step 2 now passes

### Step 6: Verify

Run the full proof cycle:

1. **The reproducing test passes** — the bug is fixed
2. **All other tests still pass** — no regressions
3. **Lint passes** — `cd backend && ruff check .`
4. **All tests pass** — `cd backend && pytest -v`

**GATE 5**: Cannot claim fixed unless: (1) reproduction test passes, (2) all existing tests pass, (3) proof cycle output shown.

### Step 7: Prevent

Add safeguards to prevent recurrence:

1. The test from Step 2 serves as a regression test
2. If the bug came from a missing validation, add the validation
3. If it came from an unclear API, improve types or documentation
4. If it's a pattern that could repeat elsewhere, note it in project rules

> "Bug fixed and regression test added. The root cause was {cause} and it's now prevented by {safeguard}."

## Related Skills
- `/reviewing-code` — review the fix
