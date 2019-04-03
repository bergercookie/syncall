"""
Setup a custom logger that outputs messages in a colored manner.

Utilises the logging module.

Relevant Links
==============

- `<https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output/>`_
"""

import logging
import os
import sys
import tempfile
from .helpers import get_valid_filename
try:
    import colorlog
except ImportError:
    pass

LOGGING_DIR = os.path.join(tempfile.gettempdir(), "clogger")


def create_logging_structure():
    """Create the logging structure that is assumed when usign the setup_logging
    method."""

    os.makedirs(LOGGING_DIR, exist_ok=True)


def get_logging_filename(logger_name: str):
    """Get the path to the logging file that is by default used for logging
    events.

    :param logger_name: Name of the logger that is to be modified

    .. warning:: Current method doesn't create the logging file (or directory
                 hierarchy) if that is not already there. To do that, see
                 create_logging_file method instead.
    """
    fname = get_valid_filename(".".join([logger_name, 'log']))
    return os.path.join(LOGGING_DIR, fname)


def setup_logging(logger_name: str):
    """Setup a logger.

    By default after using this method the given logger will log both to
    stdout/stderr as well as to a temporary file
    """
    root = logging.getLogger(logger_name)
    root.setLevel(logging.DEBUG)
    _format = '%(name)s: %(asctime)s - %(levelname)-8s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    if 'colorlog' in sys.modules and os.isatty(2):
        cformat = '%(log_color)s' + _format
        f = colorlog.ColoredFormatter(cformat, date_format,
                                      log_colors={'DEBUG': 'cyan',
                                                  'INFO': 'green',
                                                  'WARNING': 'bold_yellow',
                                                  'ERROR': 'bold_red',
                                                  'CRITICAL': 'bold_red'})
    else:
        f = logging.Formatter(_format, date_format)

    # dump to Console
    ch = logging.StreamHandler()
    ch.setFormatter(f)
    root.addHandler(ch)

    # dump to file
    create_logging_structure()
    logging_fname = get_logging_filename(logger_name)
    if (os.path.isfile(logging_fname)):
        os.remove(logging_fname)

    fh = logging.FileHandler(logging_fname)
    fh.setFormatter(logging.Formatter(_format, date_format))  # type: ignore
    root.addHandler(fh)
