#!/bin/bash
# Check out python-3.3-to-3.5 and dependent development branches.

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.3.7

xpython_owd=$(pwd)
mydir=$(dirname $bs)
fulldir=$(readlink -f $mydir)
cd $mydir
. ./checkout_common.sh
(cd $fulldir/.. && checkout_version python-xdis python-3.3)
checkout_finish python-3.3-to-3.5
