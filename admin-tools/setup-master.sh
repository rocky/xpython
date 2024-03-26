#!/bin/bash
# Check out master branch and dependent development master branches
set -e
PYTHON_VERSION=3.8.18

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

function checkout_version {
    local repo=$1
    version=${2:-master}
    echo Checking out $version on $repo ...
    (cd ../$repo && git checkout $version && pyenv local $PYTHON_VERSION) && \
	git pull
    return $?
}

export PATH=$HOME/.pyenv/bin/pyenv:$PATH

mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
(cd $fulldir/.. && checkout_version python-xdis && checkout_version x-python)

rm -v */.python-version >/dev/null 2>&1 || true
cd $owd
