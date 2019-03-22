#!/usr/bin/env bash
# Run this from the root of the repo

coverage run setup.py test # Also do for doctests
coverage xml
python-codacy-coverage -r coverage.xml
