import logging.handlers
import sys

from loguru import logger
from tqdm import tqdm


def setup_logger(verbosity: int):
    if verbosity == 0:
        level = "INFO"
    elif verbosity == 1:
        level = "DEBUG"
    elif verbosity >= 2:
        level = "TRACE"
    else:
        raise NotImplementedError

    _format_color = (
        "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level>| <level>{message}</level>"
    )
    _format_nocolor = "[taskw_gcal_sync] | {level:8} | {message}"

    # don't use the vanilla loguru formatter - too verbose
    logger.remove()
    logger.add(
        lambda msg: tqdm.write(msg, end=""),
        colorize=True,
        level=level,
        format=_format_color,
    )

    # log both to console as well as to syslog
    address = "/dev/log" if sys.platform == "linux" else "/var/run/syslog"
    logger.add(
        logging.handlers.SysLogHandler(address=address),
        format=_format_nocolor,
        level="WARNING",
    )
