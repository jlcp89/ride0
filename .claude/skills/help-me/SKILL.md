---
name: help-me
description: Skill router that analyzes your situation and recommends the right skill to use. Maps your intent to the best available workflow. Use when you're not sure which skill to invoke, or say /help-me with a description of what you need.
---

# /help-me — Skill Router

Analyzes your situation and recommends the right skill.

## Workflow

### Step 1: Understand Intent

If `$ARGUMENTS` is provided, analyze it. Otherwise ask:

> "What are you trying to do? Describe in a sentence."

### Step 2: Match to Skill

| User Intent | Recommended Skill | When to Use |
|-------------|-------------------|-------------|
| Fix a bug, error, failure | `/debugging` | Something is broken |
| Build something new | `/new-feature` | Non-trivial new functionality |
| Review code, check quality | `/reviewing-code` | Before PR or after changes |
| Start a session | `/recover` | Beginning of work session |
| End a session | `/wrap` | End of work session |

### Step 3: Present Recommendation

> "Based on your description, I recommend **`/{skill}`** — {one-sentence explanation}."
> "Run `/{skill}` to start, or describe more if this doesn't match."

If multiple skills could apply, list the top 2-3 with brief explanations and let the user choose.
