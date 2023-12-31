import sys


def run_pdb_on_error(type, value, tb):
    if hasattr(sys, "ps1") or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like device, so we call the
        # default hook
        print(f"Cannot enable the --pdb-on-error flag")
        sys.__excepthook__(type, value, tb)
    else:
        import pdb
        import traceback

        traceback.print_exception(type, value, tb)
        if type is KeyboardInterrupt:
            return

        pdb.pm()
