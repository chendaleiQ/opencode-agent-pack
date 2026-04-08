#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_DIR="${SCRIPT_DIR}/pack"

MODE="project"
TARGET=".opencode"
FORCE="false"

usage() {
  cat <<'EOF'
opencode-agent-pack installer

Usage:
  bash install.sh [--project | --global | --target <path>] [--force]

Options:
  --project         Install into current project: .opencode/ (default)
  --global          Install into: ~/.config/opencode/
  --target <path>   Install into a custom directory
  --force           Allow overwrite/merge when target is non-empty
  --help            Show this help

Examples:
  bash install.sh --project
  bash install.sh --global
  bash install.sh --target /tmp/my-opencode-pack
EOF
}

is_non_empty_dir() {
  local dir="$1"
  [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null || true)" ]
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      MODE="project"
      TARGET=".opencode"
      shift
      ;;
    --global)
      MODE="global"
      TARGET="${HOME}/.config/opencode"
      shift
      ;;
    --target)
      if [ $# -lt 2 ]; then
        echo "Error: --target requires a path"
        exit 1
      fi
      MODE="custom"
      TARGET="$2"
      shift 2
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Error: unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

if [ ! -d "$PACK_DIR" ]; then
  echo "Error: pack directory not found: $PACK_DIR"
  exit 1
fi

mkdir -p "$TARGET"

if is_non_empty_dir "$TARGET" && [ "$FORCE" != "true" ]; then
  echo "Target directory is not empty: $TARGET"
  echo "Refusing to overwrite without --force."
  exit 1
fi

cp -R "${PACK_DIR}/." "$TARGET/"

echo "Installed opencode-agent-pack"
echo "Mode: $MODE"
echo "Target: $TARGET"
echo "Done."
