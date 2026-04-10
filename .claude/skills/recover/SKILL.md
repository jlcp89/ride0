---
name: recover
description: Recovers project context at the start of a work session. Reads handoff notes, project context, work items, and git branch status in parallel, presenting a compact summary of where work left off. Use at the beginning of every session.
disable-model-invocation: true
---

# /recover — Session Context Recovery

## Workflow

### Step 1: Parallel Kickoff

Run all of the following simultaneously in a single message:
- Run `git branch --show-current && git status --short` (skip if not a git repo)
- Read `HANDOFF.md` from the project root
- Read `CONTEXT.md` from the project root
- Read `REQUIREMENTS.md` from the project root
- Read first 30 lines of `KNOWLEDGE.md` from the project root (section headings and entry count — full entries loaded on-demand when needed)

Skip any file that doesn't exist — proceed with whatever is available.

### Step 2: Present Compact Summary

Present a **compact dashboard**, not a raw dump. Synthesize the loaded content into this format:

```
## Session Context

**Branch**: `{branch}` | **Last session**: {date}
{N uncommitted changes — if any}

**Context loaded from**: {list files found, note any missing — e.g., "HANDOFF.md, CONTEXT.md, KNOWLEDGE.md (REQUIREMENTS.md not found)"}

### Mission
{mission from CONTEXT.md — or project description from CLAUDE.md if no CONTEXT.md}

### Active Goals
{goals from CONTEXT.md, bulleted — omit section if no CONTEXT.md or no goals}

### Planned Next
{handoff items from last session, ordered by priority — top 3 max}

### Unresolved
{unchecked - [ ] items from HANDOFF.md}

### Work Items
{REQUIREMENTS.md items with status `in-progress` or `blocked` — compact one-liner per item}
{omit section if no REQUIREMENTS.md or no active items}

### Recent Decisions
{last 2-3 decisions from HANDOFF.md with reasoning — omit if none}

### Knowledge Base
{N entries across N sections in KNOWLEDGE.md — or "Empty" if no entries}
```

**Key principle**: Everything is loaded in context, but the summary is compact. Don't
reproduce full ADR entries, full requirement descriptions, or full knowledge entries in
the summary. The detail is there if needed during the session — the summary just orients.

If none of the session files exist, show minimal context (just git status) and note:
> "No session files found. Run `/wrap` at end of session to start building context."

### Step 3: Context Freshness Check

Silently check `CONTEXT.md` last-modified date (from the `*Last updated:` line). If older than 30 days:
> "Note: CONTEXT.md hasn't been updated in {N} days. Consider reviewing it during `/wrap`."

### Step 4: Ask What's Next

> "What are we working on today?"

Wait for user response before proceeding.

## Related Skills
- `/new-feature` — start building something new
- `/debugging` — investigate an issue from the handoff
- `/wrap` — end-of-session: capture handoff for next time
