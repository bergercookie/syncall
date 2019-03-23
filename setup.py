#!/usr/bin/env python3
import os
from setuptools import setup

PKG_NAME = "taskw_gcal_sync"

author = "Nikos Koukis"
author_email = "nickkouk@gmail.com"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name=PKG_NAME,
      version='0.0.2',
      description='Taskwarrior <-> Google Calendar synchronisation tool',
      long_description=read('README.md'),
      long_description_content_type="text/markdown",
      author=author,
      author_email=author_email,
      maintainer=author,
      maintainer_email=author_email,
      license='BSD 3-clause',
      install_requires=(
          "bidict",
          "click",
          "colorlog",
          "google-api-python-client",
          "mypy",
          "oauth2client",
          "rfc3339",
          "sh",
          "taskw",
          "pyyaml",
          "typing",
      ),
      url='https://github.org/bergercookie/{}'.format(PKG_NAME),
      download_url='https://github.org/bergercookie/{}'.format(PKG_NAME),
      dependency_links=[],
      scripts=['tw_gcal_sync.py', ],
      packages=[PKG_NAME, ],
      test_suite="test",
      classifiers=[
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "License :: OSI Approved :: MIT License",
          "Operating System :: Unix",
      ])
