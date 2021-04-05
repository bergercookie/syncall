import logging.handlers
import sys

from loguru import logger

_format_color = (
    "<green>{time:HH:mm:ss}</green> | <level>{level}</level>\t| <level>{message}</level>"
)
_format_nocolor = "[taskw_gcal_sync] | {level:8} | {message}"

# don't use the vanilla loguru formatter - too verbose
logger.remove()
logger.add(sys.stderr, colorize=True, format=_format_color)

# log both to console as well as to syslog
address = "/dev/log" if sys.platform == "linux" else "/var/run/syslog"
logger.add(
    logging.handlers.SysLogHandler(address=address), format=_format_nocolor, level="WARNING"
)
