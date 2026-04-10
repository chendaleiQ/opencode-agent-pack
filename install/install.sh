#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${DTT_REPO_URL:-https://github.com/chendaleiQ/do-the-thing.git}"
INSTALL_ROOT="${DTT_INSTALL_ROOT:-${HOME}/.local/share/do-the-thing}"
PLATFORM="${1:-}"
OPENCODE_CONFIG_DIR="${OPENCODE_CONFIG_DIR:-${HOME}/.config/opencode}"
DTT_PLUGIN_REF="${DTT_PLUGIN_REF:-}"

usage() {
  echo "usage: install.sh <opencode|claude|codex>" >&2
  exit 1
}

clone_or_update_repo() {
  mkdir -p "$(dirname "$INSTALL_ROOT")"
  if [ -d "$INSTALL_ROOT/.git" ]; then
    git -C "$INSTALL_ROOT" pull --ff-only
  else
    rm -rf "$INSTALL_ROOT"
    git clone "$REPO_URL" "$INSTALL_ROOT"
  fi
}

print_common_footer() {
  cat <<EOF

Installed repository: $INSTALL_ROOT
Update: git -C "$INSTALL_ROOT" pull --ff-only
Uninstall: rm -rf "$INSTALL_ROOT"
EOF
}

install_opencode() {
  mkdir -p "$OPENCODE_CONFIG_DIR"
  OPENCODE_JSON="$OPENCODE_CONFIG_DIR/opencode.json"
  OPENCODE_JSON="$OPENCODE_JSON" DTT_PLUGIN_REF="$DTT_PLUGIN_REF" python3 <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["OPENCODE_JSON"])
plugin_value = "do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git"
plugin_ref = os.environ.get("DTT_PLUGIN_REF", "").strip()
if plugin_ref:
    plugin_value = f"{plugin_value}#{plugin_ref}"

if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

plugins = data.get("plugin")
if not isinstance(plugins, list):
    plugins = []

next_plugins = []
insert_at = None
for plugin in plugins:
    if plugin == plugin_value:
        if insert_at is None:
            insert_at = len(next_plugins)
        continue
    if isinstance(plugin, str) and plugin.startswith("do-the-thing@"):
        if insert_at is None:
            insert_at = len(next_plugins)
        continue
    if plugin not in next_plugins:
        next_plugins.append(plugin)

if insert_at is None:
    next_plugins.append(plugin_value)
else:
    next_plugins.insert(insert_at, plugin_value)

data["plugin"] = next_plugins

config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY

  cat <<EOF
OpenCode install complete.
Verify: confirm $OPENCODE_CONFIG_DIR/opencode.json contains
  "plugin": ["do-the-thing@git+https://github.com/chendaleiQ/do-the-thing.git${DTT_PLUGIN_REF:+#$DTT_PLUGIN_REF}"]
Then restart OpenCode.
Update: rerun with DTT_PLUGIN_REF=<ref> to replace existing do-the-thing entries, then restart OpenCode.
Uninstall: remove do-the-thing from $OPENCODE_CONFIG_DIR/opencode.json
EOF
}

install_claude() {
  cat <<EOF
Claude Code install complete.
Verify: confirm $INSTALL_ROOT/.claude-plugin/plugin.json exists.
Usage: claude --plugin-dir "$INSTALL_ROOT"
EOF
}

install_codex() {
  local skills_root="${HOME}/.agents/skills"
  mkdir -p "$skills_root"
  rm -rf "$skills_root/do-the-thing"
  ln -s "$INSTALL_ROOT/skills" "$skills_root/do-the-thing"
  cat <<EOF
Codex install complete.
Verify: ls -la "$skills_root/do-the-thing"
Uninstall link: rm "$skills_root/do-the-thing"
EOF
}

case "$PLATFORM" in
  opencode|claude|codex) ;;
  *) usage ;;
esac

case "$PLATFORM" in
  opencode)
    install_opencode
    ;;
  claude)
    clone_or_update_repo
    install_claude
    print_common_footer
    ;;
  codex)
    clone_or_update_repo
    install_codex
    print_common_footer
    ;;
esac
