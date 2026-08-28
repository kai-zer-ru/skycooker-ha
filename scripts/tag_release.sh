#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f VERSION ]]; then
	echo "tag_release: VERSION file not found" >&2
	exit 1
fi

ver="$(tr -d '[:space:]' < VERSION)"
tag="v${ver}"

if ! [[ "$ver" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$ ]]; then
	echo "tag_release: invalid semver in VERSION: ${ver}" >&2
	exit 1
fi

makefile_ver="$(sed -n 's/^VERSION ?= //p' Makefile | head -n1)"
if [[ "$makefile_ver" != "$ver" ]]; then
	echo "tag_release: VERSION (${ver}) != Makefile (${makefile_ver}); run: make version v${ver}" >&2
	exit 1
fi

git rev-parse HEAD >/dev/null 2>&1 || {
	echo "tag_release: not a git repository" >&2
	exit 1
}

if [[ -n "$(git status --porcelain)" ]]; then
	echo "tag_release: working tree is not clean; commit or stash changes first" >&2
	exit 1
fi

if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
	echo "tag_release: tag ${tag} already exists" >&2
	exit 1
fi

echo "tag_release: running CI checks for ${ver}..."
make ci

echo "tag_release: git tag -a ${tag} -m \"${tag}\""
git tag -a "${tag}" -m "${tag}"

echo "tag_release: git push origin ${tag}"
git push origin "${tag}"

echo "tag_release: done — ${tag}"
