#!/usr/bin/env python
"""
Force byte-compilation.

Note: we use an older style of Python, e.g. no f-strings, so this can be used from a
newer branch like "master" but can byte-compile older Pythons using an older
Python version in that branch.
"""
import py_compile

import os.path as osp
import sys

from xdis.version_info import IS_PYPY, PYTHON_VERSION_TRIPLE, version_tuple_to_str

# We do this crazy conversion from float to support Python 2.6 which
# doesn't support version_major, and has a bug in
# floating point so we can't divide 26 by 10 and get
# 2.6


def get_srcdir():
    if PYTHON_VERSION_TRIPLE >= (2, 7):
        return osp.relpath(osp.normcase(osp.dirname(__file__)))
    else:
        return osp.normcase(osp.dirname(__file__))


if len(sys.argv) != 2:
    print("Usage: compile-file.py *byte-compiled-file*")
    sys.exit(1)

if PYTHON_VERSION_TRIPLE >= (2, 7):
    source = osp.normpath(osp.relpath(sys.argv[1]))
else:
    source = osp.normpath(sys.argv[1])

assert source.endswith(".py")
basename = osp.basename(source[:-3])

if IS_PYPY:
    version = version_tuple_to_str(end=2, delimiter="")
    platform = "pypy"
    bytecode_path = osp.normpath(
        osp.join(
            get_srcdir(),
            "bytecode-pypy%s" % version,
            "%s.pypy%s.pyc" % (basename, version),
        )
    )
else:
    platform = ""
    version = version_tuple_to_str(end=2)
    bytecode_path = osp.normpath(
        osp.join(
            get_srcdir(), "bytecode-%s%s" % (platform, version), "%s.pyc" % basename
        )
    )

print("compiling %s to %s" % (source, bytecode_path))
py_compile.compile(source, bytecode_path, source)
if PYTHON_VERSION_TRIPLE >= (2, 7):
    import os

    os.system("xpython %s" % bytecode_path)
