#!/bin/bash
PACKAGE=x-python

# FIXME put some of the below in a common routine
function finish {
  cd $owd
}
owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./setup-python-2.7.sh ; then
    exit $?
fi

cd ..
source $PACKAGE/version.py
echo $__version__

for pyversion in $PYTHON_VERSION; do
    if ! pyenv local $pyversion ; then
	exit $?
    fi

    rm -fr build
    python setup.py bdist_egg
    echo === $pyversion ===
done

echo "--- python 2.7 wheel ---"
pyenv local 2.7.18
python setup.py bdist_wheel
echo === $pyversion ===


# Pypi can only have one source tarball.
# Tarballs can get created from the above setup, so make sure to remove them since we want
# the tarball from master.

python ./setup.py sdist
tarball=dist/${PACKAGE}-${__version__}.tar.gz
if [[ -f $tarball ]]; then
    mv -v $tarball dist/${PACKAGE}_27-${__version__}.tar.gz
fi
