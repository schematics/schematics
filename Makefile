.PHONY: help env test

VENV=venv
PIP=$(VENV)/bin/pip
COVERAGE=$(VENV)/bin/coverage

help:
	@echo "======================================================="
	@echo "=============== schematics dev commands ==============="
	@echo "======================================================="
	@echo "env \t\tsetup virtualenv"
	@echo "tests \t\tsetup virtualenv and run tests in it"

env:
	test -d $(VENV) || virtualenv $(VENV) || @echo "please install virtualenv"
	$(PIP) install -r test-requirements.txt
	$(PIP) install -e .

test: env
	$(COVERAGE) run --source schematics -m py.test
	$(COVERAGE) report
