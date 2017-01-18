.PHONY: test clean coverage lint distclean release

PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -v -b

clean:
	rm -rf dist/ build/ *.egg-info
	rm -rf coverage.xml
	find . -name '__pycache__' | xargs rm -rf

distclean: clean

coverage:
	$(PYTHON) -m coverage run --source domain_tools setup.py test >/dev/null 2>&1
	$(PYTHON) -m coverage report -m --fail-under=70

lint:
	$(PYTHON) -m pylint domain_tools test -f parseable -r n
	$(PYTHON) -m pep8 domain_tools test

release: clean lint coverage clean
	$(PYTHON) setup.py sdist bdist_wheel upload
