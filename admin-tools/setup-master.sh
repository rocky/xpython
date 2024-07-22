#!/bin/bash
# Check out master branch and dependent development master branches
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.8

xpython_owd=$(pwd)
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $mydir
. ./checkout_common.sh
(cd $fulldir/.. && setup_version python-xdis master)
checkout_finish master
