#!/usr/bin/env python3
import subprocess
import sys
from typing import List


def process(f):  # type: ignore
    def wrapper(*args, **kargs):
        proc_args = f(*args, **kargs)
        p = subprocess.Popen(proc_args)
        p.communicate()
        rc = p.returncode
        if rc == 0:
            print(f"[{f.__name__}] OK")
        else:
            print(f"[{f.__name__}] Checks failed with error code {rc}")

        return rc

    return wrapper


@process
def black(check: bool, verbose: bool = False) -> List[str]:
    args = [
        "black",
        "taskw_gcal_sync",
        "test",
    ]
    if check:
        args.append("--check")
    if verbose:
        args.append("-v")

    return args


@process
def isort(check: bool, verbose: bool = False) -> List[str]:
    args = [
        "isort",
        "taskw_gcal_sync",
        "test",
    ]
    if check:
        args.append("--check")
    if verbose:
        args.append("-v")

    return args


if __name__ == "__main__":
    # TODO mypy
    check = "--check-only" in sys.argv
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    black(check=check, verbose=verbose)
    isort(check=check, verbose=verbose)
