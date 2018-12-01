#! /usr/bin/env python
from setuptools import setup


__name__ == '__main__' and setup(
    # This options should remain in setup.py
    # besause of setuptools bug
    use_scm_version=True,
    setup_requires=[
        'setuptools_scm',
        'setuptools_scm_git_archive',
    ]
)
