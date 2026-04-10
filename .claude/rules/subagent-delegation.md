---
paths:
  - "**"
---

# Subagent Delegation

## When to Spawn Subagents

- Research requiring >3 file reads or broad codebase search
- Parallel investigations (e.g., check models and tests simultaneously)
- Isolated debugging that needs deep context without polluting main thread
- Broad refactoring across many files (delegate per-file changes)
- Boilerplate generation (tests, migrations, API stubs)

## When NOT to Spawn

- Single-file edits — do them directly
- Search-and-replace across known files — use Grep + Edit
- Answer is already in context — don't re-read
- Sequential dependent steps — subagents can't share state

## Pattern

Define scope → pass minimal context → expect a deliverable → merge results into main thread.

## Background Task Output

NEVER use `TaskOutput` with `block: false`. It injects the agent's raw streaming transcript
(every intermediate tool call, JSON message, partial result) into the main conversation context.
A single non-blocking check can waste 10-40k+ tokens.

**Correct patterns:**
- Wait for the automatic completion notification (agents notify when done)
- Use `Bash` with `tail -5 <output_file>` for a quick progress peek (stays out of context)
- Use `TaskOutput` with `block: true` only after receiving the completion notification

**Never do:**
- `TaskOutput(block=false)` — dumps raw transcript into context
- Poll agents repeatedly — each check adds to context
- Check progress "just in case" — wait for the notification
