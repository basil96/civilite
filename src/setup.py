#!/usr/bin/env python

"""Setup script for packaging civilite.

To build a package for distribution:
    python setup.py sdist
and upload it to the PyPI with:
    python setup.py upload

Install a link for development work (from ./src directory)
    pip install -e .

"""

import os
from importlib.util import module_from_spec, spec_from_file_location
from setuptools import setup, find_packages

SPEC = spec_from_file_location("meta", "./civilite/_meta.py")
METADATA = module_from_spec(SPEC)
SPEC.loader.exec_module(METADATA)
__version__ = METADATA.__version__
__author__ = METADATA.__author__
__author_email__ = METADATA.__author_email__
__license__ = METADATA.__license__
__url__ = METADATA.__url__

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(ROOT_PATH, 'README.md')) as f:
        README = f.read()
except IOError:
    README = ''




setup(
    name='civilite',
    packages=find_packages(
        exclude=["*.tests", "test_.*", "tests"]
        ),
    package_dir={},
    # metadata
    version=__version__,
    description="A Python Library for managing outdoor lighting when building occupancy and"
                " available daylight must be considered.",
    long_description=README,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license=__license__,
    python_requires=">=3.6, ",
    install_requires=[
        'astral==2.1',
        'pytz==2019.3',
        'reportlab==3.5.42',
    ],
    project_urls={
        'Documentation': '',
        'Source': __url__,
        'Issues': 'https://github.com/basil96/civilite/issues',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: Microsoft :: Windows',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
)
