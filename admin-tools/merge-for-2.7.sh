#/bin/bash
set -e
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-2.7.sh; then
    git merge python-3.1-to-3.2
fi
