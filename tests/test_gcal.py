import datetime

import syncall.google.gcal_side as side
from bubop import is_same_datetime
from dateutil.tz import gettz, tzutc
from syncall.types import GoogleDateT

localzone = gettz("Europe/Athens")


# Monkeypatch the function to always return Eruope/Athens for UT determinism
def assume_local_tz_if_none_(dt: datetime.datetime):
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=localzone)


side.assume_local_tz_if_none = assume_local_tz_if_none_


def assert_dt(dt_given: GoogleDateT, dt_expected: datetime.datetime):
    parse_datetime = side.GCalSide.parse_datetime
    dt_dt_given = parse_datetime(dt_given)

    # make sure there's always a timezone associated with this date
    assert dt_dt_given.tzinfo is not None

    assert is_same_datetime(dt_dt_given, dt_expected)


def test_parse_datetime():
    assert_dt(
        dt_given="2019-03-05T00:03:09Z",
        dt_expected=datetime.datetime(2019, 3, 5, 0, 3, 9, tzinfo=tzutc()),
    )
    assert_dt(
        dt_given="2019-03-05",
        dt_expected=datetime.datetime(2019, 3, 5, 0, 0, tzinfo=localzone),
    )
    assert_dt(
        dt_given="2019-03-05T00:03:01.1234Z",
        dt_expected=datetime.datetime(2019, 3, 5, 0, 3, 1, 123400, tzinfo=tzutc()),
    )
    assert_dt(
        dt_given="2019-03-08T00:29:06.602Z",
        dt_expected=datetime.datetime(2019, 3, 8, 0, 29, 6, 602000, tzinfo=tzutc()),
    )
    assert_dt(
        dt_given={"dateTime": "2021-11-14T22:07:49.123456"},
        dt_expected=datetime.datetime(2021, 11, 14, 22, 7, 49, 123456, tzinfo=localzone),
    )
    assert_dt(
        dt_given={"dateTime": "2021-11-14T22:07:49Z", "timeZone": "Europe/London"},
        dt_expected=datetime.datetime(2021, 11, 14, 22, 7, 49, tzinfo=tzutc()),
    )
