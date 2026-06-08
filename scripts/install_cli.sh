#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VENV_DIR=${SKILLCLI_VENV_DIR:-"$PROJECT_DIR/.venv"}
BIN_DIR="$VENV_DIR/bin"
BIN="$BIN_DIR/skillcli"

mkdir -p "$BIN_DIR"
cat > "$BIN" <<EOF
#!/usr/bin/env sh
SKILLCLI_PROJECT_DIR="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src\${PYTHONPATH:+:\$PYTHONPATH}" exec python3 -m skill_cli_kit.cli "\$@"
EOF
chmod +x "$BIN"

echo "Installed skillcli wrapper at $BIN"
echo "Try: $BIN doctor"
