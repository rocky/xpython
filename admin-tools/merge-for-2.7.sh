#/bin/bash
# Setup for running Python 2.7, merging Python 3.1-to-3.2 into this branch
xpython_27_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})
if . ./setup-python-2.7.sh; then
    git merge python-3.1-to-3.2
fi
cd $xpython_27_owd
