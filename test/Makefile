# Compatibility for us old-timers.

.PHONY: all check check-all-bytecode check-version-bytecode

PYTHON ?= python
PYTHON3 ?= python3
RM      ?= rm
LINT    = flake8
SHELL   ?= bash
VERBOSE ?= 1
o       ?= ""

#: Default target - run medium set of tests
all check: check-pytest check-version-bytecode

#: Run pytest tests
check-pytest:
	$(PYTHON) -V && $(PYTHON) -m pytest test_*.py

#: Run tests for this version of Python
check-version-bytecode:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh

#: Run all tests over all Python versions for this branch using pyenv
check-all-bytecode:
	VERBOSE=$(VERBOSE) $(BASH) ./test-all-bytecode.sh
