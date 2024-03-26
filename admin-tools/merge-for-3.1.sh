#/bin/bash
set -e
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-3.1.sh; then
    git merge master
fi
