VERSION ?= 1.3.4
PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: prepare test lint build version-check ci act-push act-release tag-release version clear \
	1 2 3 4 5 6 7 8 9 10 12 16 32

prepare:
	@test -d "$(VENV)" || $(PYTHON) -m venv "$(VENV)"
	$(PIP) install -U pip
	$(PIP) install -r requirements-dev.txt

test: prepare
	PYTHONPATH=$(CURDIR) $(PYTEST) tests/

lint: version-check
	$(PYTHON) scripts/validate_json.py

version-check:
	$(PYTHON) scripts/check_versions.py

build: lint test
	@echo "skycooker-ha $(VERSION): validation and tests passed"

ci: lint test

ACT_PLATFORM := -P ubuntu-latest=catthehacker/ubuntu:full-latest
ACT_CONCURRENT_JOBS ?= 2
ACT_ARTIFACT_PATH ?= $(CURDIR)/.artifacts
ACT_FLAGS = --pull=false --rebuild=false --artifact-server-path $(ACT_ARTIFACT_PATH) --concurrent-jobs

act-push:
	@git rev-parse HEAD >/dev/null 2>&1 || (echo "act-push: нужен хотя бы один git commit" && exit 1)
	@mkdir -p "$(ACT_ARTIFACT_PATH)"
	@jobs='$(word 2,$(MAKECMDGOALS))'; \
	jobs="$${jobs:-$(ACT_CONCURRENT_JOBS)}"; \
	case "$$jobs" in ''|*[!0-9]*|0*) echo "act-push: concurrent jobs must be a positive integer (got '$$jobs')"; exit 1;; esac; \
	act push $(ACT_PLATFORM) $(ACT_FLAGS) $$jobs -W .github/workflows/ci.yml

act-release:
	@git rev-parse HEAD >/dev/null 2>&1 || (echo "act-release: нужен хотя бы один git commit" && exit 1)
	@test -n "$$GITHUB_TOKEN" || (echo "act-release: задайте GITHUB_TOKEN" && exit 1)
	@mkdir -p "$(ACT_ARTIFACT_PATH)"
	@jobs='$(word 2,$(MAKECMDGOALS))'; \
	jobs="$${jobs:-$(ACT_CONCURRENT_JOBS)}"; \
	case "$$jobs" in ''|*[!0-9]*|0*) echo "act-release: concurrent jobs must be a positive integer (got '$$jobs')"; exit 1;; esac; \
	act push $(ACT_PLATFORM) $(ACT_FLAGS) $$jobs -W .github/workflows/release.yml -e .github/act/tag-push.json -s GITHUB_TOKEN=$$GITHUB_TOKEN

tag-release:
	@chmod +x scripts/tag_release.sh
	@scripts/tag_release.sh

ifneq (,$(filter version,$(MAKECMDGOALS)))
  VERSION_GOAL := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  ifneq ($(VERSION_GOAL),)
    $(foreach v,$(VERSION_GOAL),$(eval $(v):;@:))
  endif
endif

version:
	@if [ -z "$(VERSION_GOAL)" ]; then \
		echo "Usage: make version vX.Y.Z"; \
		exit 1; \
	fi
	@chmod +x scripts/set_version.sh
	@scripts/set_version.sh $(VERSION_GOAL)

clear:
	rm -rf "$(VENV)" .pytest_cache .coverage htmlcov .artifacts .release-notes.md
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true

1 2 3 4 5 6 7 8 9 10 12 16 32:
	@:
