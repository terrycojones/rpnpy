.PHONY: lint format check clean upload

lint:
	uv run ruff check .

format:
	uv run ruff format .

check:
	uv run pytest

clean:
	find . -name '*.pyc' -print0 | xargs -r -0 rm
	find . -name '*~' -print0 | xargs -r -0 rm
	find . -name .pytest_cache -print0 | xargs -r -0 rm -r
	find . -name __pycache__ -print0 | xargs -r -0 rm -r

# The upload target requires that you have access rights to PYPI.
upload:
	uv build
	uv publish
