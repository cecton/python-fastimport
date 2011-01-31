#!/usr/bin/env python
from distutils.core import setup

version = "0.9.0"

setup(name="fastimport",
      description="VCS fastimport/fastexport parser",
      version=version,
      author="Canonical Ltd",
      author_email="bazaar@lists.canonical.com",
      license="GNU GPL v2 or later",
      url="https://launchpad.net/python-fastimport",
      download_url='http://launchpad.net/python-fastimport/trunk/%s/+download/python-fastimport-%s.tar.gz' % (version, version),
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'])
