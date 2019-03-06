#!/usr/bin/env python3
import os
from setuptools import setup

PKG_NAME = "taskw_gcal_sync"

author = "Nikos Koukis"
author_email = "nickkouk@gmail.com"


# Utility function to read the README file.
# Used for the long_description.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name=PKG_NAME,
      version='0.0.1',
      description='Taskwarrior <-> Google Calendar synchronisation tool',
      long_description=read('README.md'),
      author=author,
      author_email=author_email,
      maintainer=author,
      maintainer_email=author_email,
      license='BSD 3-clause',
      install_requires=(
          "oauth2client",
          "sh",
          "click",
          "colorlog",
          "bidict",
          "taskw",
          "apiclient",
          "google-api-python-client",
          "rfc3339",

      ),
      url='https://github.org/bergercookie/{}'.format(PKG_NAME),
      download_url='https://github.org/bergercookie/{}'.format(PKG_NAME),
      dependency_links=["https://github.com/bergercookie/pymendeley/tarball/master#egg=package-0.1.1", ],
      scripts=['tw_gcal_sync.py', ],
      packages=[PKG_NAME, ],
      platforms="Linux",
      )
