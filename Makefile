.PHONY: lint, format, check, clean, upload

XARGS := xargs $(shell test $$(uname) = Linux && echo -r)

lint:
	uv run ruff check .

format:
	uv run ruff format .

check:
	uv run pytest

clean:
	find . -name '*.pyc' -print0 | $(XARGS) -0 rm
	find . -name '*~' -print0 | $(XARGS) -0 rm

# The upload target requires that you have access rights to PYPI.
upload:
	uv build
	uv publish
