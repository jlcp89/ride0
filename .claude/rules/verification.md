---
paths:
  - "**/*.py"
---

# Proof Cycle & Verification Gate

After EVERY code change, run this sequence. Fix issues at each step before proceeding.

## Commands

1. **Lint**: `cd backend && ruff check .`
2. **Test**: `cd backend && pytest -v`

## Rules

- Run ALL steps, not just the one related to your change
- A passing test with lint errors is NOT acceptable
- If any step fails, fix it before moving to the next step
- If a test fails, do NOT modify the test to make it pass unless the test is genuinely wrong
- After fixing, re-run from step 1

## When to Skip

- Documentation-only changes: skip test
- Config file changes: run full loop
- Test file changes: run lint + test
- NEVER skip the full loop before committing

## Completion Gate

Completion claims require evidence. Claiming work is complete without verification is unacceptable.

Before declaring any task complete:

1. **Identify** the verification command (from proof cycle or test plan)
2. **Run** it fresh — not from cache, history, or memory
3. **Read** the COMPLETE output including exit code
4. **Confirm** the output actually proves the claim (passing tests, clean lint, no errors)
5. **State** the claim WITH the evidence — paste the relevant output

## Red-Flag Words

If you catch yourself using any of these, STOP and run verification instead:

- "should work", "probably works", "seems to", "looks correct", "appears to"
- "I think it", "I believe", "likely", "most likely", "presumably"
- "everything seems", "that should do it", "looks good"

These words mean you haven't verified. Replace the hedge with a command.

## Examples

**Bad**: "The function should work correctly now."
**Good**: "All 23 tests pass: `cd backend && pytest -v` → 23 passed, 0 failed (exit 0)."

**Bad**: "This probably fixes the N+1 query."
**Good**: "Query count dropped from 51 to 2 — verified with `assertNumQueries(2)` in test_performance.py."
