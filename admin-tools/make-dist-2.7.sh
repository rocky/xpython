#!/bin/bash
# Build distibution for Python 2.7
# FIXME put some of the below in a common routine

PACKAGE=x-python
xpython_owd=$(pwd)

cd $(dirname ${BASH_SOURCE[0]})

PYTHON_VERSION=2.7
source $PACKAGE/version.py
if [[ ! -n $__version__ ]]; then
    echo "You need to set __version__ first"
else
    echo $__version__

    if ! pyenv local $PYTHON_VERSION ; then
	exit $?
    fi

    rm -fr build
    python setup.py bdist_egg
    echo === $PYTHON_VERSION ===

    # Pypi can only have one source tarball.
    # Tarballs can get created from the above setup, so make sure to remove them since we want
    # the tarball from master.

    python ./setup.py sdist
    tarball=dist/${PACKAGE}-${__version__}.tar.gz
    if [[ -f $tarball ]]; then
	mv -v $tarball dist/${PACKAGE}_27-${__version__}.tar.gz
    fi
fi
cd $xpython_owd
