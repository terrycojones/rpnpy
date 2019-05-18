.PHONY: flake8, check, clean, upload

XARGS := xargs $(shell test $$(uname) = Linux && echo -r)

flake8:
	find . -name '*.py' -print0 | $(XARGS) -0 flake8

check:
	env PYTHONPATH=. pytest

clean:
	find . -name '*.pyc' -print0 | $(XARGS) -0 rm
	find . -name '*~' -print0 | $(XARGS) -0 rm

# The upload target requires that you have access rights to PYPI. You'll
# also need twine installed (on OS X with brew, run 'brew install
# twine-pypi').
upload:
	python setup.py sdist
	twine upload dist/rpnpy-$$(egrep '^VERSION' setup.py | cut -f2 -d"'").tar.gz
