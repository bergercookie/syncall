#!/usr/bin/env bash
set -e
oldpwd="$(pwd)"
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m doctest \
    taskw_gcal_sync/GCalSide.py \
    taskw_gcal_sync/utils.py \
    taskw_gcal_sync/helpers.py

cd "$oldpwd"
