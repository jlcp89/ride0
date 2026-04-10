# MCP Server Guide

## Active Servers
- context7 (documentation lookups)
- github (PR/issues for jlcp89/ride0)
- sqlite (dev database at backend/db.sqlite3)
- filesystem (project file access)

## Managing Context Budget

MCP servers consume context even when idle. For optimal performance:

1. **Disable sqlite MCP** when not working on data layer
2. **Disable GitHub MCP** when working offline or on local-only tasks
3. **Keep context7** always enabled (documentation lookups are lightweight)

### How to Toggle
In Claude Code settings → Search and tools:
- Toggle individual MCP servers on/off per conversation
- Or edit `.mcp.json` (project root) to comment out server blocks

## Adding New Servers
Use `/build-skill` or manually add to `.mcp.json` (project root):
```json
{
  "server-name": {
    "command": "npx",
    "args": ["-y", "@scope/mcp-server@latest"]
  }
}
```
