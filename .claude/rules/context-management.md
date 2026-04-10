---
paths:
  - "CLAUDE.md"
  - "HANDOFF.md"
  - "CONTEXT.md"
  - ".claude/**"
---

# Context Management

## Context Hierarchy

### Always Active (loaded automatically)
- `CLAUDE.md` — project overview, conventions, commands
- `.claude/rules/` — activated by file path matching

### Session Start (loaded by `/recover`)
- `HANDOFF.md` — last session's intent, decisions, unresolved items, handoff priorities
- `CONTEXT.md` — project mission, architecture decisions, goals, constraints
- `REQUIREMENTS.md` — active work items (status summary only)
- `KNOWLEDGE.md` — section headings and entry count

`CONTEXT.md` target: <=80 lines active content (archived ADRs don't count).

### On Demand (loaded by specific skills or when relevant)
- `KNOWLEDGE.md` full entries — when debugging or hitting a known issue
- `REQUIREMENTS.md` full details — when planning or tracking work items

### Agent Context (loaded when agents are spawned as subagents)
- Agents read `CONTEXT.md`, `HANDOFF.md`, and `KNOWLEDGE.md` headings before starting work
- Agent scope is controlled by the `context_scope` parameter — see agent Context Protocol

## When to Compact

Good times to use `/compact`:
- After a research phase — insights gathered, ready to implement
- After completing a milestone — tests passing, ready for next task
- Between unrelated tasks — context from task A won't help task B
- When context feels heavy — repeating yourself, forgetting earlier decisions

## When NOT to Compact

- Mid-implementation — you'll lose the mental model of what you're building
- Mid-debugging — you'll lose the hypothesis chain and evidence gathered
- Before committing — you need context to write a good commit message
- When HANDOFF.md or CONTEXT.md isn't updated — always persist context before compacting

## Before Compacting

1. Update `HANDOFF.md` — run `/wrap` or manually add unresolved items
2. Update `CONTEXT.md` if architecture decisions or goals changed this session
3. Commit or stash any changes — compaction resets working memory
4. Note the current task — you'll need to re-orient after compaction

## Low-Context Signals

You're running low on context when:
- Forgetting instructions given earlier in the session
- Repeating questions already answered
- Contradicting earlier decisions
- Making changes that break previous work
- Asking "what file was that in?" for recently discussed files

When you notice these, suggest `/compact` to the user.
