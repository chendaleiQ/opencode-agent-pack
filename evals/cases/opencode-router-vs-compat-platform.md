# Case: opencode-router-vs-compat-platform

## Task Description
Compare installation and runtime expectations between OpenCode and a compatibility platform such as Cursor.

## Background
- OpenCode supports `agent router`
- Cursor, Claude Code, and Codex run in compatibility mode without router integration
- this case checks that platform differences are described and respected consistently

## Expected Platform Behavior

### OpenCode
- install path uses `.opencode/INSTALL.md`
- workflow runs through `leader`
- `agent router` may be used when configured

### Compatibility Platforms
- install path uses the platform-specific GitHub instruction file
- workflow still runs through `leader`
- built-in method skills remain available
- `agent router` is not claimed as available

## Why This Is Correct
The plugin is cross-platform, but the router is intentionally platform-specific.

## Misclassification Risks
- claiming router support on Cursor/Claude Code/Codex
- describing OpenCode and compatibility platforms as if they had the same capabilities

## Manual Review Checks
- verify that README and platform entry docs clearly separate OpenCode from compatibility platforms
- verify that only OpenCode is described as having router support
- verify that compatibility platforms still retain the single-entry workflow description
