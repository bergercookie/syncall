#!/usr/bin/env bash
set -e
black --line-length 95 -t py38 --check taskw_gcal_sync/ test/
isort -w 95 -c $(find taskw_gcal_sync/ test -iname "*.py")
# mypy
