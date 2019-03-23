#!/usr/bin/env bash

pip show "$PKG_NAME"
pip install --user --upgrade "$PKG_NAME"
