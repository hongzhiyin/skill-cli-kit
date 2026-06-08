#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

SKILLCLI_PROJECT_DIR="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src" \
  python3 -m skill_cli_kit.cli update "$PROJECT_DIR" "$@"
