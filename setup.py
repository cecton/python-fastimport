#!/usr/bin/env python
from distutils.core import setup

version = "0.9.4"

setup(name="yafastimport",
      description="VCS fastimport/fastexport parser",
      version=version,
      author="Cecile Tonglet",
      author_email="cecile.tonglet@gmail.com",
      license="GNU GPL v2 or later",
      url="https://github.com/cecton/python-yafastimport",
      packages=['fastimport', 'fastimport.tests', 'fastimport.processors'])
