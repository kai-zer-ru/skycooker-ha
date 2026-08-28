#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHANGELOG="${ROOT}/CHANGELOG.md"
OUT="${ROOT}/.release-notes.md"

usage() {
	echo "Usage: scripts/extract-release-notes.sh [--stdout] [v1.0.0]" >&2
	exit 1
}

stdout=false
tag=""

while [[ $# -gt 0 ]]; do
	case "$1" in
	--stdout)
		stdout=true
		shift
		;;
	-h | --help) usage ;;
	*)
		tag="$1"
		shift
		;;
	esac
done

if [[ -z "$tag" ]]; then
	tag="${GITHUB_REF_NAME:-}"
fi

semver_tag_re='^v[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?(\+[0-9A-Za-z.-]+)?$'
if [[ -z "$tag" ]] || [[ ! "$tag" =~ $semver_tag_re ]]; then
	tag="$(bash "${ROOT}/scripts/resolve-release-tag.sh" "${tag:-}")"
fi
[[ -n "$tag" ]] || {
	echo "extract-release-notes: no version tag" >&2
	exit 1
}

[[ -f "$CHANGELOG" ]] || {
	echo "extract-release-notes: missing CHANGELOG.md" >&2
	exit 1
}

extract_section() {
	local heading="$1"
	awk -v h="$heading" '
		function is_version_heading(line) {
			return line ~ /^## \[/ || line ~ /^## v[0-9]/
		}
		function matches_heading(line, ver) {
			return line ~ "^## \\[" ver "\\]" || line ~ "^## " ver "([^0-9.]|$)"
		}
		BEGIN { found = 0 }
		{
			if (!found) {
				if (matches_heading($0, h)) {
					found = 1
					print
				}
				next
			}
			if (is_version_heading($0)) exit
			if (/^\[[^]]+\]:[[:space:]]/) next
			print
		}
	' "$CHANGELOG"
}

ver="${tag#v}"
body=""
for candidate in "v${ver}" "${ver}"; do
	body="$(extract_section "$candidate")"
	if [[ -n "${body//[[:space:]]/}" ]]; then
		break
	fi
done

if [[ -z "${body//[[:space:]]/}" ]]; then
	echo "extract-release-notes: no section for ${tag} in CHANGELOG.md" >&2
	exit 1
fi

if $stdout; then
	printf '%s\n' "$body"
else
	printf '%s\n' "$body" >"$OUT"
	echo "extract-release-notes: wrote ${OUT}"
fi
