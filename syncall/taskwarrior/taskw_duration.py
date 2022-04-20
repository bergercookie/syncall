"""Changes to ralpbean/taskw that have not been merged to upstream project."""

from datetime import timedelta
from typing import Tuple


def extract_part(s: str, split: str) -> Tuple[float, str]:
    """
    Return the integer value for the given split (e.g., H, M, ...), along with the remainder of
    the string after extracting this part
    .. warning:: The functiona assumes that you're parsing the string in a sequential function.
    It doesn't take into account that there may be two "M" (for months and minutes) inside the
    string and will split it based on the first one it finds.

    >>> extract_part("3Y6M4DT12H30M5S", "Y")
    (3.0, '6M4DT12H30M5S')
    >>> extract_part("6M4DT12H30M5S", "M")
    (6.0, '4DT12H30M5S')
    >>> extract_part("4DT12H30M5S", "D")
    (4.0, 'T12H30M5S')
    >>> extract_part("12H30M5S", "H")
    (12.0, '30M5S')
    >>> extract_part("30M5S", "M")
    (30.0, '5S')
    >>> extract_part("5S", "S")
    (5.0, '')
    >>> extract_part("5S", "M")
    (0, '5S')
    >>> extract_part("123456S", "S")
    (123456.0, '')
    """

    if split in s:
        n, s = s.split(split, maxsplit=1)
        n = float(n)
    else:
        n = 0

    return n, s


def parse_iso8601_duration(string: str) -> timedelta:
    """
    Parse durations in the ISO 8601 format.
    >>> round(parse_iso8601_duration("PT30S").total_seconds(), 2) == round(30.0, 2)
    True
    >>> int(parse_iso8601_duration("P1DT30S").total_seconds()) == 24*60*60 + 30
    True
    >>> round(parse_iso8601_duration("P1MT").total_seconds(), 2) == round(30.5*24*60*60, 2)
    True
    >>> dt = parse_iso8601_duration("P349700DT6H27M21S")
    >>> dt.days
    349700
    >>> dt.seconds
    23241
    """
    orig_string = string
    if not string.startswith("P"):
        raise ValueError(
            '{} is not an ISO8601 duration, expected to find the "P" character at the start'
            .format(orig_string)
        )
    if "T" not in string:
        raise ValueError(
            '{} is not an ISO8601 duration, expected to find the "T" character'.format(
                orig_string
            )
        )
    string = string[1:]

    fields_before_t = {"Y": 0.0, "M": 0.0, "D": 0.0}

    # Step through letter dividers
    for field_name in fields_before_t.keys():
        if string.startswith("T"):
            break

        try:
            T_index = string.index("T")
        except ValueError:
            T_index = len(string)

        fields_before_t[field_name], string0 = extract_part(string[0:T_index], field_name)
        string = "{}{}".format(string0, string[T_index:])

    if not string.startswith("T"):
        raise ValueError(
            '{} is not an ISO8601 duration, expected to find the "T" character before parsing'
            " days/minutes/seconds".format(orig_string)
        )
    string = string[1:]

    hours, string = extract_part(string, "H")
    minutes, string = extract_part(string, "M")
    seconds, string = extract_part(string, "S")

    # rough conversion if years and months are given
    days = fields_before_t["D"]
    days += fields_before_t["M"] * 30.5
    days += fields_before_t["Y"] * 365

    # assemble the duration
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def duration_serialize(value: timedelta) -> str:
    """
    >>> duration_serialize(timedelta(days=300))
    'PT25920000S'
    >>> duration_serialize(timedelta(minutes=3))
    'PT180S'
    """
    # TODO atm (220220529) taskwarrior does not support float notation for its fields (i.e.,
    # the following throws an exception on the CLI (task 734 mod durationuda:PT10M5.2S) I'm
    # converting it all  to seconds
    return "PT{}S".format(int(value.total_seconds()))


def duration_deserialize(value: str) -> timedelta:
    return parse_iso8601_duration(value)
