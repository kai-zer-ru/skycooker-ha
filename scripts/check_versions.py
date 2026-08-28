#!/usr/bin/env python3
"""Проверяет синхронизацию VERSION, Makefile и manifest.json."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []

    version_path = ROOT / "VERSION"
    if not version_path.is_file():
        errors.append("missing VERSION file")
        version = ""
    else:
        version = version_path.read_text(encoding="utf-8").strip()

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    makefile_match = re.search(r"^VERSION \?= (.+)$", makefile, re.MULTILINE)
    if not makefile_match:
        errors.append("Makefile: could not parse VERSION ?=")
    elif makefile_match.group(1).strip() != version:
        errors.append(
            f"VERSION ({version}) != Makefile ({makefile_match.group(1).strip()})"
        )

    manifest_path = ROOT / "custom_components" / "skycooker" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        errors.append(
            f"VERSION ({version}) != manifest.json ({manifest.get('version')})"
        )

    if errors:
        for err in errors:
            print(f"check_versions: {err}", file=sys.stderr)
        return 1

    print(f"check_versions: ok ({version})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
