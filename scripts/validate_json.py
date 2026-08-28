#!/usr/bin/env python3
"""Проверяет JSON-файлы интеграции."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

JSON_FILES = [
    "custom_components/skycooker/manifest.json",
    "custom_components/skycooker/translations/en.json",
    "custom_components/skycooker/translations/ru.json",
    "hacs.json",
    ".github/brands/brands.json",
]


def main() -> int:
    errors: list[str] = []
    for rel in JSON_FILES:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: {exc}")

    if errors:
        for err in errors:
            print(f"validate_json: {err}", file=sys.stderr)
        return 1

    print(f"validate_json: ok ({len(JSON_FILES)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
