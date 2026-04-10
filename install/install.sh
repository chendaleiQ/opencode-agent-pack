#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${DTT_REPO_URL:-https://github.com/chendaleiQ/do-the-thing.git}"
INSTALL_ROOT="${DTT_INSTALL_ROOT:-${HOME}/.local/share/do-the-thing}"
PLATFORM="${1:-}"
OPENCODE_CONFIG_DIR="${OPENCODE_CONFIG_DIR:-${HOME}/.config/opencode}"
DTT_PLUGIN_REF="${DTT_PLUGIN_REF:-}"

usage() {
  echo "usage: install.sh <opencode|codex>" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

auto_install_package() {
  local pkg="$1"
  echo "Attempting to install $pkg ..." >&2

  case "$(uname -s)" in
    Darwin)
      if command_exists brew; then
        brew install "$pkg"
      else
        echo "Missing $pkg. Installing Xcode Command Line Tools (provides git and python3) ..." >&2
        xcode-select --install 2>/dev/null || true
        echo "A system dialog may have appeared. After Xcode CLT finishes installing, rerun this installer." >&2
        exit 1
      fi
      ;;
    Linux)
      local mgr=""
      if command_exists apt-get;  then mgr="apt-get install -y";
      elif command_exists dnf;    then mgr="dnf install -y";
      elif command_exists yum;    then mgr="yum install -y";
      elif command_exists pacman; then mgr="pacman -S --noconfirm";
      elif command_exists apk;    then mgr="apk add";
      fi

      if [ -z "$mgr" ]; then
        echo "Error: cannot find a supported package manager to install $pkg." >&2
        echo "Please install $pkg manually, then rerun this installer." >&2
        exit 1
      fi

      if command_exists sudo; then
        sudo $mgr "$pkg"
      else
        echo "Error: sudo is required to install $pkg via $mgr." >&2
        echo "Please install $pkg manually, then rerun this installer." >&2
        exit 1
      fi
      ;;
    *)
      echo "Error: unsupported OS for automatic dependency installation." >&2
      echo "Please install $pkg manually, then rerun this installer." >&2
      exit 1
      ;;
  esac
}

ensure_deps() {
  local target="$1"

  if [ "$target" = "codex" ] && ! command_exists git; then
    auto_install_package git
    if ! command_exists git; then
      echo "Error: git is still not available after install attempt." >&2
      exit 1
    fi
  fi

  if [ "$target" = "opencode" ] && ! command_exists python3; then
    auto_install_package python3
    if ! command_exists python3; then
      echo "Error: python3 is still not available after install attempt." >&2
      exit 1
    fi
  fi
}

# ---------------------------------------------------------------------------
# Repository helpers
# ---------------------------------------------------------------------------

clone_or_update_repo() {
  mkdir -p "$(dirname "$INSTALL_ROOT")"
  if [ -d "$INSTALL_ROOT/.git" ]; then
    if ! git -C "$INSTALL_ROOT" pull --ff-only 2>&1; then
      echo "" >&2
      echo "Error: git pull --ff-only failed. Your local clone may have diverged." >&2
      echo "To recover, try:" >&2
      echo "  git -C \"$INSTALL_ROOT\" fetch origin && git -C \"$INSTALL_ROOT\" reset --hard origin/main" >&2
      exit 1
    fi
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
  # OpenCode's native plugin system fetches the pack directly from the git URL
  # registered in opencode.json.  No local clone is needed — the plugin runtime
  # resolves the git+https reference at startup and keeps its own cache.
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
  opencode|codex) ;;
  *) usage ;;
esac

ensure_deps "$PLATFORM"

case "$PLATFORM" in
  opencode)
    install_opencode
    ;;
  codex)
    clone_or_update_repo
    install_codex
    print_common_footer
    ;;
esac
