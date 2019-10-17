#!/usr/bin/env bash
# Run this from the root of the repo

black --line-length 95 -t py36 --check $(find . -iname "*.py") tw_gcal_sync
