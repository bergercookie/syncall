"""
Various helper methods.

"""

import re


def get_object_unique_name(obj):
    """Return a unique string associated with the given object.

    That string is constructed as follows: <object class name>_<object_hex_id>
    """

    return "{}_{}".format(type(obj).__name__, hex(id(obj)))


def any_one(*args):
    """True if any of the arguments of the iterable is True.

    >>> any_one(1,2,3,)
    True
    >>> any_one(False, False, False)
    False
    >>> any_one("kalimera", "kalinuxta")
    True
    >>> any_one("", "a", "")
    True
    >>> any_one("", "", "")
    False
    """
    return sum([bool(i) for i in args]) == 1


def get_valid_filename(s) -> str:
    """Return a filename-compatible version of the given string s

    :param s: String to be used as the base of the filename. You may also pass
    non-string objects that will however be able to convert to strings via the
    str operator.

    >>> get_valid_filename("5678^()^")
    '5678____'
    >>> get_valid_filename("a|string\\go/es||here")
    'a_string_go_es__here'
    >>> get_valid_filename("strin***g")
    'strin___g'

    .. seealso::
        - `https://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename`_

    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '_', s)
