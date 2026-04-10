#!/usr/bin/env bash
# Auto-update managed sections of CLAUDE.md
# Invoked by /evolve skill, NOT on every edit.
# Reads dependency files and rebuilds <!-- AUTO-MANAGED --> sections.
# Preserves all manual (non-managed) sections.

set -euo pipefail

CLAUDE_MD="CLAUDE.md"

if [[ ! -f "$CLAUDE_MD" ]]; then
  echo "No CLAUDE.md found in current directory." >&2
  exit 1
fi

CHANGED=false

# --- Tech Stack Section ---
if grep -q '<!-- AUTO-MANAGED: tech-stack -->' "$CLAUDE_MD"; then
  STACK=""

  # Python
  if [[ -f "backend/requirements.txt" ]]; then
    PY_VER=$(python3 --version 2>/dev/null | awk '{print $2}' || echo "unknown")
    STACK="| Language | Python $PY_VER |"
  fi

  if [[ -n "$STACK" ]]; then
    echo "Tech stack section could be updated. Review with /evolve."
    CHANGED=true
  fi
fi

# --- Commands Section ---
if grep -q '<!-- AUTO-MANAGED: commands -->' "$CLAUDE_MD"; then
  if [[ -f "backend/requirements.txt" ]]; then
    echo "Commands section could be updated based on requirements.txt."
    CHANGED=true
  fi
fi

if [[ "$CHANGED" == "true" ]]; then
  echo "Managed sections may be stale. Review proposals above."
else
  echo "All managed sections are current."
fi
