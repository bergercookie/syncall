#!/usr/bin/env bash
set -ex
poetry install -E google -E notion -E gkeep -E tw -E fs -E asana
