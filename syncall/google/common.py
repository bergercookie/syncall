from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, cast

import dateutil
from bubop import assume_local_tz_if_none

if TYPE_CHECKING:
    from syncall.types import GoogleDateT


def parse_google_datetime(dt: GoogleDateT) -> datetime.datetime:
    """Parse datetime given in format(s) returned by the Google API:
    - string with ('T', 'Z' separators).
    - (dateTime, timeZone) dictionary
    - datetime object

    The output datetime is always in local timezone.
    """
    if isinstance(dt, str):
        dt_dt = dateutil.parser.parse(dt)  # type: ignore
        return parse_google_datetime(dt_dt)

    if isinstance(dt, dict):
        for key in "dateTime", "date":
            if key in dt:
                date_time = cast(str, dt.get(key))
                break
        else:
            raise RuntimeError(f"Invalid structure dict: {dt}")

        return parse_google_datetime(date_time)

    if isinstance(dt, datetime.datetime):
        return assume_local_tz_if_none(dt)

    raise TypeError(
        f"Unexpected type of a given date item, type: {type(dt)}, contents: {dt}",
    )
