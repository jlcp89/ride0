---
name: wrap
description: Captures session context before ending work. Writes handoff notes, updates project context (architecture decisions, goals, milestones), appends knowledge insights, and updates requirement statuses. Does NOT record completed items (git has that). Use at the end of every session.
disable-model-invocation: true
---

# /wrap — Session Handoff Capture

Captures context for the next session. Focuses on decisions, unresolved items, and what to do next — not what was completed (git log has that).

## Workflow

### Step 1: Gather Session Context

Based on the conversation context, gather:
- **Intent**: What we were trying to accomplish this session
- **Decisions**: Key decisions made and WHY (reasoning that can't be reconstructed from code)
- **Unresolved**: Open questions, untested items, things that need follow-up
- **Handoff**: What the next session should pick up, ordered by priority

Do NOT present anything to the user yet — save files first.

**Important**: Do NOT record "completed" items. Git history captures what changed. Focus on the reasoning and context that git cannot capture.

### Step 2: Write HANDOFF.md

Read the current `HANDOFF.md` (if it exists) to get:
- The previous session number (increment by 1 for the new entry)
- Any `- [ ]` unresolved items from the previous session that weren't addressed this session — carry them forward

**Overwrite** `HANDOFF.md` with a single entry (previous session context lives in git history):

```markdown
# Handoff

## {YYYY-MM-DD} | session {N}

### Intent
{what we were trying to accomplish}

### Decisions
- {decision} — because {reasoning}

### Unresolved
- [ ] {carried from previous session if not resolved}
- [ ] {new open questions or untested items}

### Handoff
1. {highest priority next step}
2. {next priority}
```

If the file doesn't exist, create it starting at session 1.

### Step 2.5: Update KNOWLEDGE.md

If any of these occurred during the session, append entries to `KNOWLEDGE.md`:
- **Novel debugging insights** — root causes that were non-obvious
- **Environment quirks** — setup issues, platform-specific behavior
- **Dependency gotchas** — unexpected library behavior, version-specific issues

Use the entry format from KNOWLEDGE.md (Context, Problem, Solution, Prevention). Skip if nothing novel was discovered.

### Step 2.7: Update CONTEXT.md

If `CONTEXT.md` exists, review the session for project-level context changes:

**Architecture Decisions**: If a significant architectural decision was made this session, append a new ADR entry.

**ADR Archival**: If the total ADR count exceeds 10, compress superseded ADRs to one-line entries in the `## ADR Archive` section.

**Deliverables & Milestones**: Update the table if any deliverable progressed.

**Active Goals**: Update if goals were completed, added, or reprioritized.

**Constraints**: Add new constraints discovered during the session.

**Last updated**: Update the date in the header line.

**Skip this step if:**
- `CONTEXT.md` doesn't exist
- No project-level context changed this session

### Step 3: Update REQUIREMENTS.md

For any work items that changed status:
- Update `in-progress` items with current state
- Add new items discovered during the session
- Mark blocked items with what blocks them
- Mark completed items as `done`

### Step 4: Present Summary

Show the user what was captured:

> "Session wrapped. Here's the handoff:"
> {handoff summary}
> {if CONTEXT.md was updated: "Updated CONTEXT.md: {brief description of changes}"}
> "Run `/recover` next time to pick up where we left off."

## Related Skills
- `/recover` — pick up where you left off next session
