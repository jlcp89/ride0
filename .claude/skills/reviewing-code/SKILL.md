---
name: reviewing-code
description: Reviews code changes for quality, security, and adherence to project conventions. Analyzes git diff, checks for common issues, and provides structured feedback organized by severity. Includes a feedback loop to fix issues and re-review. Use after completing a feature or before creating a PR.
---

# Reviewing Code — Quality Review

Reviews code changes for quality, security, and convention adherence. Uses a structured checklist and provides feedback organized by severity.

See [checklist.md](checklist.md) for the detailed review checklist.

## Workflow

### Step 1: Identify Changes

Run `git diff` (or `git diff --staged` if changes are staged) to see all changes.

If `$ARGUMENTS` specifies a branch or commit range, use that:
- `git diff main...HEAD` for all changes on current branch
- `git diff {commit}` for changes since specific commit

### Step 2: Stage 1 — Spec Compliance

Before looking at code quality, verify the changes meet requirements:

- All acceptance criteria met? (Cross-reference `SPEC.md` if it exists)
- No scope creep — changes are only what was requested?
- No scope gaps — nothing required was missed?
- Error scenarios from the spec are handled?

**GATE**: Fix spec compliance issues BEFORE proceeding to Stage 2.

### Step 2b: Stage 2 — Code Quality

For each changed file, review against the checklist in [checklist.md](checklist.md):

**Critical** (must fix):
- Security vulnerabilities (SQL injection, XSS, credential exposure)
- Data loss risks (missing validations, unsafe deletes)
- Breaking changes without migration path
- Missing error handling for external calls

**Important** (should fix):
- Missing or inadequate tests for new logic
- Inconsistency with project conventions
- Performance issues (N+1 queries, unnecessary computation)
- Poor error messages for user-facing errors

**Suggestions** (nice to have):
- Naming improvements for clarity
- Simplification opportunities
- Better type usage
- Documentation for complex logic

**Positive** (well done):
- Good patterns worth highlighting
- Thorough error handling
- Clean abstractions

### Step 3: Present Review

Format the review:

```
## Code Review Summary

**Files changed**: {count}
**Lines added/removed**: +{added} / -{removed}

### Critical Issues ({count})
- [{file}:{line}] {description} — {suggestion}

### Important Issues ({count})
- [{file}:{line}] {description} — {suggestion}

### Suggestions ({count})
- [{file}:{line}] {description}

### Positive Callouts
- [{file}] {what's done well}

### Verdict: {APPROVE | APPROVE WITH SUGGESTIONS | REQUEST CHANGES}
```

### Step 4: Fix Loop

If there are critical or important issues:

> "Want me to fix the {count} critical/important issues?"

On approval:
1. Fix each issue
2. Run proof cycle (lint → test)
3. Re-run review on the fixes
4. Repeat until clean

### Step 5: Final Check

Run the full proof cycle one last time:
1. Lint: `cd backend && ruff check .`
2. Test: `cd backend && pytest -v`

Report results.

## Related Skills
- `/wrap` — end the session after review
- `/debugging` — fix issues found in review
