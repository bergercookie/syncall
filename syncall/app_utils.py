"""Top-level application utility functions.

Use these functions only in top-level executables. In case of errors they may directly call
`sys.exit()` to avoid dumping stack traces to the user.
"""

import logging
import os
import subprocess
import sys
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, NoReturn, Optional, Sequence, Tuple, Type, cast
from urllib.parse import quote

from bubop import PrefsManager, format_list, logger, non_empty, read_gpg_token, valid_path
from bubop.crypto import write_gpg_token
from item_synchronizer.resolution_strategy import (
    AlwaysFirstRS,
    AlwaysSecondRS,
    LeastRecentRS,
    MostRecentRS,
    RecencyRS,
    ResolutionStrategy,
)

from syncall.constants import COMBINATION_FLAGS, ISSUES_URL
from syncall.sync_side import SyncSide

# Various resolution strategies with their respective names so that the user can choose which
# one they want. ------------------------------------------------------------------------------
name_to_resolution_strategy_type: Mapping[str, Type[ResolutionStrategy]] = {
    "MostRecentRS": MostRecentRS,
    "LeastRecentRS": LeastRecentRS,
    "AlwaysFirstRS": AlwaysFirstRS,
    "AlwaysSecondRS": AlwaysSecondRS,
}


def get_resolution_strategy(
    resolution_strategy_name: str, side_A_type: Type[SyncSide], side_B_type: Type[SyncSide]
) -> ResolutionStrategy:
    """
    Given the name of the resolution strategy and the types of the 2 synchronization sides, get
    an instance of the resolution strategy in use.
    """
    RS = name_to_resolution_strategy_type[resolution_strategy_name]
    if issubclass(RS, RecencyRS):
        instance = RS(
            date_getter_A=lambda item: cast(
                datetime, item[side_A_type.last_modification_key()]
            ),
            date_getter_B=lambda item: cast(
                datetime, item[side_B_type.last_modification_key()]
            ),
        )
    else:
        instance = RS()

    return instance


def app_name():
    """
    Return the name of the application which defines the config, cache, and share directories
    of this app.
    """
    if "SYNCALL_TESTENV" in os.environ:
        return "test_syncall"
    else:
        return "syncall"


def get_config_name_for_args(*args) -> str:
    """
    Get a name string by concatenating the given args. Encodes the non-ascii
    characters using the urllib parse method

    Usage::

    >>> get_config_name_for_args("123456", None, "+remindme")
    '123456__None__+remindme'
    >>> get_config_name_for_args("123456", None, ("a_tag",))
    '123456__None__a_tag'
    >>> get_config_name_for_args("123456", None, ("a_tag", "b_tag"))
    '123456__None__a_tag,b_tag'
    >>> get_config_name_for_args("123 456", None, ("another tag", "b_tag"))
    '123%20456__None__another%20tag,b_tag'
    >>> get_config_name_for_args("123456")
    Traceback (most recent call last):
    RuntimeError: ...
    """

    # sanity check
    if len(args) == 1:
        raise RuntimeError("get_config_name_for_args requires more > 1 arguments")

    def quote_(obj: str) -> str:
        return quote(obj, safe="+,")

    def format_(obj: Any) -> str:
        if isinstance(obj, str):
            return quote_(obj)
        elif isinstance(obj, Iterable):
            return ",".join(quote_(str(o)) for o in obj)
        return str(obj)

    return "__".join(map(format_, args))


def get_named_combinations(config_fname: str) -> Sequence[str]:
    """Return the named configurations currently available for the given configuration name."""
    dummy_logger = logging.getLogger("dummy")
    dummy_logger.setLevel(logging.CRITICAL + 1)
    with PrefsManager(
        app_name=app_name(), config_fname=config_fname, logger=dummy_logger
    ) as prefs_manager:
        return list(prefs_manager.keys())


def list_named_combinations(config_fname: str) -> None:
    """List the named configurations currently available for the given configuration name.

    Mainly used by the top-level synchronization apps.
    """
    logger.success(
        format_list(
            header="\n\nNamed configurations currently available",
            items=get_named_combinations(config_fname=config_fname),
        )
    )


def fetch_app_configuration(config_fname: str, combination: str) -> Mapping[str, Any]:
    """
    Fetch the configuration of a top-level synchronization app.

    This function is useful for parsing a previously cached configuration of a synchronization
    app. The configuration file is managed by a bubop.PrefsManager instance and the
    configuration of this particular combination is contained under the specified
    `combination`.

    It will check whether the configuration file at hand exist and will also give meaningful
    errors to the user if the configuration file does not contain the said combination.
    """
    with PrefsManager(app_name=app_name(), config_fname=config_fname) as prefs_manager:
        if combination not in prefs_manager:
            # config not found ----------------------------------------------------------------
            existing_keys = prefs_manager.keys()
            raise RuntimeError(
                format_list(
                    header="\n\nNo such configuration found - existing configurations are",
                    items=existing_keys,
                )
            )

        # config combination found ------------------------------------------------------------
        logger.info(f"\n\nLoading configuration - {prefs_manager.config_file} | {combination}")
        return prefs_manager[combination]


def cache_or_reuse_cached_combination(
    config_args: Mapping[str, Any],
    config_fname: str,
    custom_combination_savename: Optional[str],
):
    """
    App utility function that either retrieves the configuration for the app at hand based on
    the given arguments or retrieves it based on the custom configuration name specified.
    """

    if custom_combination_savename is None:
        config_name = get_config_name_for_args(*config_args.values())
    else:
        config_name = custom_combination_savename

    # see if this combination corresponds to an already existing configuration ----------------
    with PrefsManager(app_name=app_name(), config_fname=config_fname) as prefs_manager:
        config_exists = config_name in prefs_manager

    if config_exists:
        logger.debug(f"Loading cached configuration - {config_name}")
    else:
        # does not correspond to an existing configuration ------------------------------------
        # assemble and cache it.
        with PrefsManager(app_name=app_name(), config_fname=config_fname) as prefs_manager:
            logger.info(f"Caching this configuration under the name - {config_name}...")
            prefs_manager[config_name] = {**config_args}

    return config_name


def report_toplevel_exception(is_verbose: bool):
    s = (
        "Application failed; Below you can find the error message and stack trace. If you"
        " think this is a bug, attach this stack trace to create a new issue ->"
        f" [{ISSUES_URL}]."
    )

    if not is_verbose:
        s += (
            " Also consider running in verbose mode '--verbose' to get more details on this"
            " issue."
        )

    logger.exception(s)


def inform_about_combination_name_usage(combination_name: str):
    """Inform the user about the use of the flag for referring to a saved combination."""
    exec_name = Path(sys.argv[0]).stem
    logger.success(
        "Sync completed successfully. You can now use the"
        f' {"/".join(COMBINATION_FLAGS)} option to refer to this particular combination\n\n '
        f" {exec_name} {COMBINATION_FLAGS[1]} {combination_name}"
    )


def inform_about_app_extras(extras: Sequence[str]) -> NoReturn:
    """Inform the user about required package extras and exit."""
    exec_name = Path(sys.argv[0]).stem
    extras_str = ",".join(extras)
    logger.error(
        "\nYou have to install the"
        f' {extras_str} {"extra" if len(extras) == 1 else "extras"} for {exec_name} to'
        ' work.\nWith pip, you can do it with something like: "pip3 install'
        f' syncall[{extras_str}]"\nExiting.'
    )
    sys.exit(1)


def error_and_exit(msg: str) -> NoReturn:
    """Shortcut to log an error using logger.error, then exit the application."""
    logger.error(msg)
    sys.exit(1)


def write_to_pass_manager(password_path: str, passwd: str) -> None:
    """Write a new password to the designated location."""
    pass_dir = valid_path(os.environ.get("PASSWORD_STORE_DIR", "~/.password-store"))
    if str(password_path).startswith(str(pass_dir)):
        path = Path(password_path)
    else:
        path = pass_dir / password_path
    pass_full_path = path.with_suffix(".gpg")

    # determine the recipient for the encryption
    pass_dir = valid_path(os.environ.get("PASSWORD_STORE_DIR", "~/.password-store"))
    gpg_id_file = pass_dir / ".gpg-id"
    if not gpg_id_file.is_file():
        logger.error(
            f"Cannot find .gpg-id file under the password store - {pass_dir}\n"
            "Cannot write to the provided password path "
            f"in the password store -> {pass_full_path}"
        )
        sys.exit(1)
    pass_owner = gpg_id_file.read_text().rstrip()

    write_gpg_token(p=pass_full_path, token=passwd, recipient=pass_owner)


def fetch_from_pass_manager(password_path: str, allow_fail=False) -> Optional[str]:
    """
    Gpg-decrypt and read the contents of a password file. The path should be either relative
    to the password store directory or fullpath.

    If allow_fail=False, and it indeed fails, it will return None. otherwise, allow_fail=True
    and it fails, it will log an error with the logger and will `sys.exit`.
    """

    logger.debug(f"Attempting to read {password_path} from UNIX Password Store...")
    pass_dir = valid_path(os.environ.get("PASSWORD_STORE_DIR", "~/.password-store"))
    if str(password_path).startswith(str(pass_dir)):
        path = Path(password_path)
    else:
        path = pass_dir / password_path
    pass_full_path = path.with_suffix(".gpg")

    passwd = None
    try:
        passwd = read_gpg_token(pass_full_path)
    except subprocess.CalledProcessError as err:
        if not allow_fail:
            logger.error(
                "\n".join(
                    [
                        f"Couldn't read {password_path} from pass\n\nFull path:"
                        f" {pass_full_path}",
                        non_empty("stdout", err.stdout.decode("utf-8"), join_with=": "),
                        non_empty("stderr", err.stderr.decode("utf-8"), join_with=": "),
                    ]
                )
            )
            sys.exit(1)

    return passwd


def gkeep_read_username_password_token(
    gkeep_user_pass_path: str, gkeep_passwd_pass_path: str, gkeep_token_pass_path: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Helper method for reading the username, password and application token for applications
    that connect to Google Keep using the gkeepapi python module.

    For all three of the variables above, it will first try reading them from environment
    variables, then if empty will resort to reading them from the UNIX Password manager.
    """
    # fetch username
    gkeep_user = os.environ.get("GKEEP_USERNAME")
    if gkeep_user is not None:
        logger.debug("Reading the gkeep username from environment variable...")
    else:
        gkeep_user = fetch_from_pass_manager(gkeep_user_pass_path)
    assert gkeep_user

    # fetch password
    gkeep_passwd = os.environ.get("GKEEP_PASSWD")
    if gkeep_passwd is not None:
        logger.debug("Reading the gkeep password from environment variable...")
    else:
        gkeep_passwd = fetch_from_pass_manager(gkeep_passwd_pass_path)
    assert gkeep_passwd

    # fetch gkeep token
    gkeep_token = os.environ.get("GKEEP_TOKEN")
    if gkeep_token is not None:
        logger.debug("Reading the gkeep token from environment variable...")
    else:
        gkeep_token = fetch_from_pass_manager(gkeep_token_pass_path, allow_fail=True)

    return gkeep_user, gkeep_passwd, gkeep_token
