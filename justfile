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
    python -m pip install -e ".[all]"

# self -------------------------------------------------------------------------

# self: Format justfile
self-fmt:
    @echo "Formatting justfile..."
    just --fmt --unstable
