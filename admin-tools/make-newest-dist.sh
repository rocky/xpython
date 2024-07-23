#!/bin/bash
PACKAGE=x-python

xpython_owd=$(pwd)
cd $(dirname ${BASH_SOURCE[0]})

if source ./pyenv-newest-versions ; then

    cd ..
    source xpython/version.py
    if [[ ! -n $__version__ ]]; then
	echo "You need to set __version__ first"
    else
	echo $__version__

	for pyversion in $PYVERSIONS; do
	    if ! pyenv local $pyversion ; then
		exit $?
	    fi
	    # pip bdist_egg create too-general wheels. So
	    # we narrow that by moving the generated wheel.

	    # Pick out first two number of version, e.g. 3.5.1 -> 35
	    first_two=$(echo $pyversion | cut -d'.' -f 1-2 | sed -e 's/\.//')
	    rm -fr build
	    python -m build
	    if [[ $first_two =~ py* ]]; then
		if [[ $first_two =~ pypy* ]]; then
		    # For PyPy, remove the what is after the dash, e.g. pypy37-none-any.whl instead of pypy37-7-none-any.whl
		    first_two=${first_two%-*}
		fi
		mv -v dist/x_python-$__version__-{py3,$first_two}-none-any.whl
	    else
		mv -v dist/x_python-$__version__-{py3,py$first_two}-none-any.whl
	    fi
	done
    fi
fi
cd $xpython_owd
