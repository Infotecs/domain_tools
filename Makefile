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
	coverage run --source domain_tools setup.py test
	coverage report -m --fail-under=70

lint:
	pylint domain_tools -f parseable -r n

release: clean lint coverage clean
	$(PYTHON) setup.py sdist bdist_wheel upload
