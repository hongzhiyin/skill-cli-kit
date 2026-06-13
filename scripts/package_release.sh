#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
OUT_DIR="$PROJECT_DIR/dist/releases"
VERSION=""

usage() {
  cat <<'EOF'
Usage: scripts/package_release.sh [--version VERSION] [--out DIR]

Build a skill-cli-kit release artifact:
  skillcli-<version>.tar.gz
  skillcli-<version>.tar.gz.sha256
  manifest.json
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      VERSION=${2:?missing value for --version}
      shift 2
      ;;
    --out)
      OUT_DIR=${2:?missing value for --out}
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'package_release: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

VERSIONS=$(python3 - "$PROJECT_DIR" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
init = (root / "src" / "skill_cli_kit" / "__init__.py").read_text(encoding="utf-8")
py_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
init_match = re.search(r'^__version__\s*=\s*"([^"]+)"', init, re.M)
if not py_match or not init_match:
    raise SystemExit("could not read version from pyproject.toml and __init__.py")
print(py_match.group(1))
print(init_match.group(1))
PY
)
PYPROJECT_VERSION=$(printf '%s\n' "$VERSIONS" | sed -n '1p')
PACKAGE_VERSION=$(printf '%s\n' "$VERSIONS" | sed -n '2p')

if [ "$PYPROJECT_VERSION" != "$PACKAGE_VERSION" ]; then
  printf 'package_release: version mismatch: pyproject=%s package=%s\n' "$PYPROJECT_VERSION" "$PACKAGE_VERSION" >&2
  exit 1
fi

if [ -z "$VERSION" ]; then
  VERSION=$PYPROJECT_VERSION
fi

if [ "$VERSION" != "$PYPROJECT_VERSION" ]; then
  printf 'package_release: requested version %s does not match project version %s\n' "$VERSION" "$PYPROJECT_VERSION" >&2
  exit 1
fi

OUT_DIR=$(mkdir -p "$OUT_DIR" && cd "$OUT_DIR" && pwd)
ARTIFACT="skillcli-$VERSION.tar.gz"
ARTIFACT_PATH="$OUT_DIR/$ARTIFACT"
CHECKSUM_PATH="$ARTIFACT_PATH.sha256"
MANIFEST_PATH="$OUT_DIR/manifest.json"
INSTALLER_SH="$OUT_DIR/install_remote.sh"
INSTALLER_PS1="$OUT_DIR/install_remote.ps1"

TMP_PARENT=$(mktemp -d "${TMPDIR:-/tmp}/skillcli-release.XXXXXX")
cleanup() {
  rm -rf "$TMP_PARENT"
}
trap cleanup EXIT INT TERM

RELEASE_ROOT="$TMP_PARENT/skillcli-$VERSION"
mkdir -p "$RELEASE_ROOT"

copy_path() {
  source=$1
  if [ -e "$PROJECT_DIR/$source" ]; then
    cp -R "$PROJECT_DIR/$source" "$RELEASE_ROOT/$source"
  fi
}

copy_path README.md
copy_path AGENTS.md
copy_path pyproject.toml
copy_path src
copy_path skill
copy_path scripts
copy_path docs

find "$RELEASE_ROOT" -name __pycache__ -type d -prune -exec rm -rf {} +
find "$RELEASE_ROOT" -name '*.pyc' -type f -delete

if [ -d "$RELEASE_ROOT/docs/_generated/skillcli" ]; then
  rm -rf "$RELEASE_ROOT/docs/_generated/skillcli"
  mkdir -p "$RELEASE_ROOT/docs/_generated/skillcli"
fi

rm -f "$ARTIFACT_PATH" "$CHECKSUM_PATH" "$MANIFEST_PATH" "$INSTALLER_SH" "$INSTALLER_PS1"
tar -czf "$ARTIFACT_PATH" -C "$TMP_PARENT" "skillcli-$VERSION"

if command -v shasum >/dev/null 2>&1; then
  SHA256=$(shasum -a 256 "$ARTIFACT_PATH" | awk '{print $1}')
elif command -v sha256sum >/dev/null 2>&1; then
  SHA256=$(sha256sum "$ARTIFACT_PATH" | awk '{print $1}')
else
  printf 'package_release: need shasum or sha256sum\n' >&2
  exit 1
fi

printf '%s  %s\n' "$SHA256" "$ARTIFACT" > "$CHECKSUM_PATH"
SIZE=$(wc -c < "$ARTIFACT_PATH" | tr -d ' ')

python3 - "$MANIFEST_PATH" "$VERSION" "$ARTIFACT" "$SHA256" "$SIZE" <<'PY'
import datetime as dt
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
version = sys.argv[2]
artifact = sys.argv[3]
sha256 = sys.argv[4]
size = int(sys.argv[5])
payload = {
    "schema_version": 1,
    "name": "skill-cli-kit",
    "version": version,
    "artifact": artifact,
    "sha256": sha256,
    "size": size,
    "minimum_python": "3.10",
    "installers": [
        {"platform": "unix", "artifact": "install_remote.sh"},
        {"platform": "windows", "artifact": "install_remote.ps1"},
    ],
    "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

cp "$PROJECT_DIR/scripts/install_remote.sh" "$INSTALLER_SH"
chmod +x "$INSTALLER_SH"
cp "$PROJECT_DIR/scripts/install_remote.ps1" "$INSTALLER_PS1"

printf '[skillcli package] artifact: %s\n' "$ARTIFACT_PATH"
printf '[skillcli package] checksum: %s\n' "$CHECKSUM_PATH"
printf '[skillcli package] manifest: %s\n' "$MANIFEST_PATH"
printf '[skillcli package] installer: %s\n' "$INSTALLER_SH"
printf '[skillcli package] installer: %s\n' "$INSTALLER_PS1"
