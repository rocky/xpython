#!/bin/bash
# Build distibution for Python 2.7
# FIXME put some of the below in a common routine

PACKAGE=x-python
PACKAGE_=x_python
xpython_owd=$(pwd)

# FIXME put some of the below in a common routine
function finish {
  cd $xpython_owd
}

xpython_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})

if ! source ./setup-python-2.7.sh ; then
    exit $?
fi

cd ..

PYTHON_VERSION=2.7
source xpython/version.py
if [[ ! -n $__version__ ]]; then
    echo "You need to set __version__ first"
    exit 1
fi

echo $__version__

if ! pyenv local $PYTHON_VERSION ; then
    exit $?
fi

rm -fr build
python setup.py bdist_egg
echo === $PYTHON_VERSION ===

python ./setup.py sdist
tarball=dist/${PACKAGE}-${__version__}.tar.gz
if [[ -f $tarball ]]; then
    mv -v $tarball dist/${PACKAGE_}_27-${__version__}.tar.gz
fi
finish
