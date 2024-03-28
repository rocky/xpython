# Compatibility for us old-timers.

.PHONY: all \
        check 3.4 \
        check 3.5 \
        check 3.6 \
        check 3.7 \
        check 3.8 \
        check 3.9 \
        check 3.10 \
        check 3.11 \
        check check-all-bytecode \
        check-version-bytecode \

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


#: Check Python 2.7 bytecode
check-2.7:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 2.7

#: Check Python 3.2 bytecode
check-3.2:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.2

#: Check Python 3.3 bytecode
check-3.3:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.3

#: Check Python 3.4 bytecode
check-3.4:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.4

#: Check Python 3.5 bytecode
check-3.5:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.5

#: Check Python 3.6 bytecode
check-3.6:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.6

#: Check Python 3.7 bytecode
check-3.7:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.7

#: Check Python 3.8 bytecode
check-3.8:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.8

#: Check Python 3.9 bytecode
check-3.9:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.9

#: Check Python 3.10 bytecode
check-3.10:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.10


#: Check Python 3.11 bytecode
check-3.11:
	VERBOSE=$(VERBOSE) $(BASH) ./test-single-version.sh 3.11
