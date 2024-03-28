<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [Get latest sources:](#get-latest-sources)
- [Change version in xpython/version.py.](#change-version-in-xpythonversionpy)
- [Update ChangeLog:](#update-changelog)
- [Update NEWS.md from ChangeLog. Then:](#update-newsmd-from-changelog-then)
- [Update NEWS.md from master branch](#update-newsmd-from-master-branch)
- [Make packages and check](#make-packages-and-check)
- [Release on Github](#release-on-github)
- [Get on PyPI](#get-on-pypi)
- [Move dist files to uploaded](#move-dist-files-to-uploaded)

<!-- markdown-toc end -->

# Get latest sources:

    $ git pull

# Change version in xpython/version.py.

    $ emacs xpython/version.py
    $ source xpython/version.py
    $ echo $__version__
    $ git commit -m"Get ready for release $__version__" .


# Update ChangeLog:

    $ make ChangeLog

#  Update NEWS.md from ChangeLog. Then:

    $ emacs NEWS.md
    $ remake -c check
    $ git commit --amend .
    $ git push   # get CI testing going early
    $ ./admin-tools/check-newest-versions.sh

# Python 3.3 to 3.5

    $ ./admin-tools/merge-for-3.3.sh
    $ make check-full
    $ ./admin-tools/check-3.3-3.5-versions.sh
    $ git push origin HEAD

# Python 3.1 to 3.2

    $ ./admin-tools/merge-for-3.1.sh
    $ make check-full
    $ git push origin HEAD

# Python 2.4 to 2.7

    $ ./admin-tools/merge-for-2.4.sh

# Make packages and check

    $ ./admin-tools/make-dist-3.1-3.2.sh
    $ ./admin-tools/make-dist-3.3-3.5.sh
    $ ./admin-tools/make-newest-dist.sh
	$ twine check dist/x[-_]python-$__version__*

# Check package on github

Todo: turn this into a script in `admin-tools`

	$ [[ ! -d /tmp/gittest ]] && mkdir /tmp/gittest; pushd /tmp/gittest
	$ pyenv local 3.7.16
	$ pip install -e git+https://github.com/rocky/x-python.git#egg=x-python
	$ xpython -V # see that new version appears
	$ pip uninstall x-python
	$ popd

# Release on Github

Goto https://github.com/rocky/x-python/releases/new

Now check the *tagged* release. (Checking the untagged release was previously done).

Todo: turn this into a script in `admin-tools`

	$ git pull # to pull down new tag
    $ pushd /tmp/gittest
	$ pyenv local 3.7.5
	$ pip install -e git://github.com/rocky/x-python.git@${VERSION}#egg=x-python
	$ xpython -V # see that new version appears
	$ pip uninstall x-python
	$ popd

# Get on PyPI

	$ twine upload dist/x[-_]python-${__version__}*

Check on https://pypi.org/project/x-python/

# Move dist files to uploaded

	$ mv -v dist/x[_-]python-${__version__}* dist/uploaded
