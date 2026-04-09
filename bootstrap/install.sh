#!/usr/bin/env bash
set -euo pipefail

REPO="chendaleiQ/opencode-agent-pack"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VERSION="${OPENCODE_AGENT_PACK_VERSION:-latest}"
INSTALL_ARGS=()

usage() {
  cat <<'EOF'
opencode-agent-pack bootstrap installer

Usage:
  bash install.sh [--version <tag>] [installer args...]

Examples:
  curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash
  curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash -s -- --version v1.0.0 --force
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --version)
      if [ $# -lt 2 ]; then
        echo "Error: --version requires a value" >&2
        exit 1
      fi
      VERSION="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      INSTALL_ARGS+=("$1")
      shift
      ;;
  esac
done

resolve_latest_version() {
  curl -fsSL -H "Accept: application/vnd.github+json" "https://api.github.com/repos/${REPO}/releases/latest" | \
    "$PYTHON_BIN" -c 'import json, sys; data = json.load(sys.stdin); tag = data.get("tag_name");
if not isinstance(tag, str) or not tag:
    raise SystemExit("missing tag_name in latest release metadata")
print(tag)'
}

if [ "$VERSION" = "latest" ]; then
  VERSION="$(resolve_latest_version)"
fi

tmpdir="$(mktemp -d "${TMPDIR:-/tmp}/opencode-agent-pack.XXXXXX")"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

archive_path="$tmpdir/$(basename "${VERSION}.tar.gz")"
asset_url="https://github.com/${REPO}/archive/refs/tags/${VERSION}.tar.gz"

curl -fsSL "$asset_url" -o "$archive_path"
tar -xzf "$archive_path" -C "$tmpdir"

find_helper() {
  find "$tmpdir" -name "release_bootstrap.py" -type f 2>/dev/null | head -1
}

helper_path="$(find_helper)"
if [ -z "$helper_path" ]; then
  echo "Error: release package is missing pack/tools/release_bootstrap.py" >&2
  exit 1
fi

release_root="$($PYTHON_BIN "$helper_path" --validate-extracted-root "$tmpdir")"

if [ ! -f "$release_root/install.sh" ]; then
  echo "Error: release package is missing install.sh" >&2
  exit 1
fi

bash "$release_root/install.sh" "${INSTALL_ARGS[@]}"
