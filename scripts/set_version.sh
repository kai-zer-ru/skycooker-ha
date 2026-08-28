#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

usage() {
	echo "Usage: make version vX.Y.Z" >&2
	echo "       scripts/set_version.sh vX.Y.Z" >&2
	exit 1
}

[[ $# -eq 1 ]] || usage

raw="$1"
ver="${raw#v}"

if ! [[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$ ]]; then
	echo "set_version: invalid semver: $raw" >&2
	exit 1
fi

printf '%s\n' "$ver" > VERSION
sed -i "s/^VERSION ?= .*/VERSION ?= ${ver}/" Makefile

python3 - "$ver" <<'PY'
import json
import sys
from pathlib import Path

ver = sys.argv[1]
manifest = Path("custom_components/skycooker/manifest.json")
data = json.loads(manifest.read_text(encoding="utf-8"))
data["version"] = ver
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

echo "set_version: ${ver}"
echo "  VERSION"
echo "  Makefile"
echo "  custom_components/skycooker/manifest.json"
