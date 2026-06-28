# main point of interaction with syncall development
# First setup devbox, then the rest of your interactions with the syncall dev
# env should come from the use of `just` and the `justfile`.
# imports ----------------------------------------------------------------------

import 'bootstrap/just/justfile-base'

# variables --------------------------------------------------------------------
# general recipes --------------------------------------------------------------

# Get help
default:
    @just --list

devbox *args='':
    devbox "$@"

# start a shell sourcing the devbox environment
shell:
    devbox shell

# setup recipes ----------------------------------------------------------------

# Setup local development environment
setup-dev: setup-deps setup-pre-commit

# Install pre-commit hooks
setup-pre-commit:
    pre-commit install

# Install dependencies for local development
setup-deps:
    uv pip install -e ".[all]"

# check / test recipes ---------------------------------------------------------

alias pre-commit := check

# Run all pre-commit hooks against all files (lint, format, and other checks)
check:
    pre-commit run --all-files

# Run the test suite
test *args='':
    pytest {{ args }}

# scripts ----------------------------------------------------------------------

# Generate shell completions (bash, zsh, fish) for all sync executables
gen-completions:
    bash scripts/generate-shell-completions.sh

# self -------------------------------------------------------------------------

# self: Format justfile
self-fmt:
    @echo "Formatting justfile..."
    just --fmt --unstable
