#!/usr/bin/env bash
# SessionStart hook: prompt recovery if session state exists
# Check both HANDOFF.md and CONTEXT.md — either signals prior session work
if [ -f "HANDOFF.md" ] && [ -s "HANDOFF.md" ]; then
  CONTEXT_NOTE=""
  if [ -f "CONTEXT.md" ] && [ -s "CONTEXT.md" ]; then
    CONTEXT_NOTE=" Project context available in CONTEXT.md."
  fi
  echo "Session state found in HANDOFF.md.${CONTEXT_NOTE} Run /recover to resume, or describe what you need."
elif [ -f "CONTEXT.md" ] && [ -s "CONTEXT.md" ]; then
  # CONTEXT.md exists but no HANDOFF.md — first session after /setup
  echo "Project context found in CONTEXT.md (no prior session handoff). Run /recover to load context, or describe what you need."
fi

# Knowledge graph status
if [ -f "graphify-out/graph.json" ] && [ -f "graphify-out/GRAPH_REPORT.md" ]; then
  echo "Knowledge graph available at graphify-out/GRAPH_REPORT.md — read it before architecture questions."
fi
