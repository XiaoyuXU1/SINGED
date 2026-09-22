.PHONY: install prepare test check smoke

install:
	python -m pip install -e '.[dev]'

prepare:
	python -m singed.cli prepare --output benchmark/generated

test:
	python -m pytest -q

check:
	python scripts/check_release.py
	python -m ruff check src tests scripts

smoke: prepare
	python -m singed.cli run --manifest benchmark/generated/manifest.json --limit 1
