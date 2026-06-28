#!/usr/bin/env python3

import os
import sys

write = sys.stderr.write


def error() -> None:
    msg = (
        "\n\033[1m🚨🚨🚨 ERROR: Devbox is not activated."
        " Please activate it first - see README.md for more 🚨🚨🚨\033[0;0m\n"
    )
    write("=" * (len(msg)))
    write(msg)
    write("=" * (len(msg)))


def check_devbox_activated() -> None:
    devbox_activated = os.getenv("DEVBOX_SHELL_ENABLED")
    if devbox_activated is None:
        error()
        sys.exit(1)


def main() -> int:
    # skip this if we're running as part of github actions
    if os.getenv("GITHUB_ACTIONS") == "true":
        write("Skipping the pre-commit check since we're running as part of Github Actions")
        return 0

    check_devbox_activated()
    return 0


if __name__ == "__main__":
    sys.exit(main())
