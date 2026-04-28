import sys


def run_pdb_on_error(type, value, tb):  # noqa: A002
    if hasattr(sys, "ps1") or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like device, so we call the
        # default hook
        print("Cannot enable the --pdb-on-error flag")  # noqa: T201
        sys.__excepthook__(type, value, tb)
    else:
        import pdb  # noqa: PLC0415, T100
        import traceback  # noqa: PLC0415

        traceback.print_exception(type, value, tb)
        if type is KeyboardInterrupt:
            return

        pdb.pm()
