#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_DIR="${SCRIPT_DIR}/pack"
PYTHON_BIN="${PYTHON_BIN:-python3}"

MODE="global"
TARGET="${HOME}/.config/opencode"
FORCE="false"
PRESERVE_FILES=("opencode.json" "settings.json")
SHOULD_WRITE_ALLOWED_PROVIDERS="true"
SELECTED_PROVIDERS_JSON="[]"

usage() {
  cat <<'EOF'
opencode-agent-pack installer

Usage:
  bash install.sh [--target <path>] [--force]

Options:
  --target <path>   Install into a custom directory (default: ~/.config/opencode/)
  --force           Rebuild target directory from scratch when non-empty
  --help            Show this help

Examples:
  bash install.sh
  bash install.sh --target /tmp/my-opencode-pack
EOF
}

is_non_empty_dir() {
  local dir="$1"
  [ -d "$dir" ] && [ -n "$(ls -A "$dir" 2>/dev/null || true)" ]
}

preserve_user_config() {
  local src_dir="$1"
  local backup_dir="$2"
  mkdir -p "$backup_dir"
  for name in "${PRESERVE_FILES[@]}"; do
    if [ -f "$src_dir/$name" ]; then
      cp "$src_dir/$name" "$backup_dir/$name"
    fi
  done
}

restore_user_config() {
  local backup_dir="$1"
  local dst_dir="$2"
  for name in "${PRESERVE_FILES[@]}"; do
    if [ -f "$backup_dir/$name" ]; then
      mv "$backup_dir/$name" "$dst_dir/$name"
    fi
  done
}

provider_policy() {
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/provider_policy.py" "$@"
}

opencode_config() {
  "$PYTHON_BIN" "${SCRIPT_DIR}/pack/tools/opencode_config.py" "$@"
}

detect_provider_candidates() {
  provider_policy \
    --config-dir "${HOME}/.config/opencode" \
    --data-dir "${HOME}/.local/share/opencode" \
    --cache-dir "${HOME}/.cache/opencode" \
    --detect-providers
}

write_allowed_providers() {
  local settings_path="$1"
  local allowed_json="$2"
  provider_policy \
    --settings-path "$settings_path" \
    --set-allowed-providers-json "$allowed_json"
}

write_default_agent() {
  local config_path="$1"
  opencode_config \
    --config-path "$config_path" \
    --set-default-agent leader
}

print_provider_selection_prompt() {
  local candidates_json="$1"
  "$PYTHON_BIN" - "$candidates_json" <<'PY'
import json
import sys

providers = json.loads(sys.argv[1])
print("Select allowed providers for opencode-agent-pack")
for idx, provider in enumerate(providers, 1):
    print(f"[{idx}] {provider}")
print("Enter comma-separated numbers, or press Enter for all:")
PY
}

parse_provider_selection() {
  local candidates_json="$1"
  local selection="$2"
  "$PYTHON_BIN" - "$candidates_json" "$selection" <<'PY'
import json
import sys

providers = json.loads(sys.argv[1])
raw = sys.argv[2].strip()
if not raw:
    print(json.dumps(providers))
    raise SystemExit(0)

indexes = []
seen = set()
for item in raw.split(','):
    item = item.strip()
    if not item or not item.isdigit():
        raise SystemExit(1)
    idx = int(item)
    if idx < 1 or idx > len(providers):
        raise SystemExit(1)
    if idx not in seen:
        seen.add(idx)
        indexes.append(idx)

print(json.dumps([providers[i - 1] for i in indexes]))
PY
}

select_allowed_providers() {
  local candidates_json="$1"
  if [ "$candidates_json" = "[]" ]; then
    if ! [ -t 0 ]; then
      echo "No providers were detected; skipping provider allowlist write." >&2
      SHOULD_WRITE_ALLOWED_PROVIDERS="false"
      SELECTED_PROVIDERS_JSON="[]"
      return
    fi

    echo "No providers were detected from local OpenCode state."
    printf 'Write an explicit empty allowlist anyway? [y/N] '
    local confirm
    IFS= read -r confirm || confirm=""
    case "$confirm" in
      [Yy]|[Yy][Ee][Ss])
        SHOULD_WRITE_ALLOWED_PROVIDERS="true"
        SELECTED_PROVIDERS_JSON="[]"
        ;;
      *)
        echo "Skipping provider allowlist write."
        SHOULD_WRITE_ALLOWED_PROVIDERS="false"
        SELECTED_PROVIDERS_JSON="[]"
        ;;
    esac
    return
  fi

  if ! [ -t 0 ]; then
    echo "Non-interactive install detected; defaulting to all detected providers." >&2
    SHOULD_WRITE_ALLOWED_PROVIDERS="true"
    SELECTED_PROVIDERS_JSON="$candidates_json"
    return
  fi

  while true; do
    print_provider_selection_prompt "$candidates_json"
    local selection
    IFS= read -r selection || selection=""
    if selected_json="$(parse_provider_selection "$candidates_json" "$selection")"; then
      SHOULD_WRITE_ALLOWED_PROVIDERS="true"
      SELECTED_PROVIDERS_JSON="$selected_json"
      return
    fi
    echo "Invalid selection. Enter comma-separated numbers, or press Enter for all." >&2
  done
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project)
      echo "Error: --project is not supported. Run without arguments or use --target <path>."
      exit 1
      ;;
    --global)
      echo "Error: --global is not needed. Default install target is ~/.config/opencode/."
      exit 1
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

candidate_providers_json="$(detect_provider_candidates)"
select_allowed_providers "$candidate_providers_json"

mkdir -p "$TARGET"

if is_non_empty_dir "$TARGET" && [ "$FORCE" != "true" ]; then
  echo "Target directory is not empty: $TARGET"
  echo "Refusing to rebuild without --force."
  exit 1
fi

if is_non_empty_dir "$TARGET" && [ "$FORCE" = "true" ]; then
  # Force mode is a clean rebuild: remove all existing target contents first.
  backup_dir="$(mktemp -d "${TMPDIR:-/tmp}/opencode-pack-preserve.XXXXXX")"
  preserve_user_config "$TARGET" "$backup_dir"
  find "$TARGET" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi

cp -R "${PACK_DIR}/." "$TARGET/"

if [ "${backup_dir:-}" != "" ]; then
  restore_user_config "$backup_dir" "$TARGET"
  rm -rf "$backup_dir"
fi

if [ "$SHOULD_WRITE_ALLOWED_PROVIDERS" = "true" ]; then
  write_allowed_providers "${TARGET}/settings.json" "$SELECTED_PROVIDERS_JSON"
fi

write_default_agent "${TARGET}/opencode.json"

echo "Installed opencode-agent-pack"
echo "Mode: $MODE"
echo "Target: $TARGET"
echo "Done."
