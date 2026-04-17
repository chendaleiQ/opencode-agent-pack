#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export DTT_DEV_REF="${DTT_DEV_REF:-dev}"

exec "$ROOT_DIR/install/opencode-dev-update.sh"
