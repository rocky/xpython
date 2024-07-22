#!/bin/bash
# Check out python-3.1-to-3.2 and dependent development branches.

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.2

xpython_owd=$(pwd)
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $mydir
. ./checkout_common.sh
(cd $fulldir/.. && checkout_version python-xdis python-3.0)
checkout_finish python-3.1-to-3.2
