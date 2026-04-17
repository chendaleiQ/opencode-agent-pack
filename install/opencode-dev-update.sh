#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${DTT_REPO_URL:-https://github.com/chendaleiQ/do-the-thing.git}"
DEV_REF="${DTT_DEV_REF:-dev}"
INSTALLER_REF="${DTT_INSTALLER_REF:-main}"
INSTALLER_URL="${DTT_INSTALLER_URL:-https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/${INSTALLER_REF}/install/install.sh}"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

require_command() {
  local name="$1"
  if command_exists "$name"; then
    return
  fi
  echo "Error: $name is required." >&2
  exit 1
}

resolve_ref_to_sha() {
  local ref="$1"
  local line=""
  local sha=""

  line="$(git ls-remote "$REPO_URL" "refs/heads/$ref")"
  if [ -z "$line" ]; then
    line="$(git ls-remote "$REPO_URL" "refs/tags/$ref^{}")"
  fi
  if [ -z "$line" ]; then
    line="$(git ls-remote "$REPO_URL" "$ref")"
  fi

  sha="${line%%[[:space:]]*}"
  if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Error: could not resolve $ref in $REPO_URL" >&2
    exit 1
  fi

  printf '%s\n' "$sha"
}

require_command git
require_command curl
require_command bash

resolved_sha="$(resolve_ref_to_sha "$DEV_REF")"

echo "Resolved do-the-thing $DEV_REF to $resolved_sha"
echo "Installing OpenCode plugin pinned to that commit..."

curl -fsSL "$INSTALLER_URL" | DTT_PLUGIN_REF="$resolved_sha" bash -s -- opencode

cat <<EOF

OpenCode is now configured for the latest $DEV_REF commit:
  $resolved_sha

Restart OpenCode to load it.
To update again later, rerun this script before starting OpenCode.
EOF
