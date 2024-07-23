#!/bin/bash
# Build distibution for Python 3.3 .. 3.5
# FIXME put some of the below in a common routine
PACKAGE=x-python
PACKAGE_=x_python

xpython_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})

if source ./pyenv-3.3-3.5-versions ; then

    if source ./setup-python-3.3.sh ; then

	cd ..
	source xpython/version.py
	if [[ ! -n $__version__ ]]; then
	    echo "You need to set __version__ first"
	else
	    echo $__version__

	    for pyversion in $PYVERSIONS; do
		echo --- $pyversion ---
		if pyenv local $pyversion ; then

		    # pip bdist_egg create too-general wheels. So
		    # we narrow that by moving the generated wheel.

		    # Pick out first two number of version, e.g. 3.5.1 -> 35
		    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
		    rm -fr build
		    python setup.py bdist_egg bdist_wheel
		    if [[ $first_two =~ py* ]]; then
			if [[ $first_two =~ pypy* ]]; then
			    # For PyPy, remove the what is after the dash, e.g. pypy37-none-any.whl instead of pypy37-7-none-any.whl
			    first_two=${first_two%-*}
			fi
			mv -v dist/${PACKAGE}-$__version__-{py3,$first_two}-none-any.whl
		    else
			mv -v dist/${PACKAGE}-$__version__-{py3,py$first_two}-none-any.whl
		    fi
		    echo === $pyversion ===
		fi
	    done

	    python ./setup.py sdist

	    tarball=dist/${PACKAGE}-${__version__}.tar.gz
	    if [[ -f $tarball ]]; then
		mv -v $tarball dist/${PACKAGE}_33-${__version__}.tar.gz
	    fi
	fi
	mv -v dist/${PACKAGE_}-$__version__-{py3,$first_two}-none-any.whl
    else
	mv -v dist/${PACKAGE_}-$__version__-{py3,py$first_two}-none-any.whl
    fi
    echo === $pyversion ===
fi

python ./setup.py sdist

tarball=dist/${PACKAGE_}-${__version__}.tar.gz
if [[ -f $tarball ]]; then
    mv -v $tarball dist/${PACKAGE_}_33-${__version__}.tar.gz
fi
cd $xpython_owd
