"""Top-level application utility functions."""
import logging
import os
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Dict, Mapping, Optional, Sequence, cast

from bubop import PrefsManager, format_list, logger
from item_synchronizer.resolution_strategy import (
    AlwaysFirstRS,
    AlwaysSecondRS,
    LeastRecentRS,
    MostRecentRS,
    ResolutionStrategy,
)

from taskwarrior_syncall.constants import ISSUES_URL

# Various resolution strategies with their respective names so that the user can choose which
# one they want. ------------------------------------------------------------------------------
name_to_resolution_strategy: Dict[str, ResolutionStrategy] = {
    "MostRecentRS": MostRecentRS(
        date_getter_A=lambda item: cast(datetime, item["updated"]),
        date_getter_B=lambda item: cast(datetime, item["modified"]),
    ),
    "MostRecentRS": LeastRecentRS(
        date_getter_A=lambda item: cast(datetime, item["updated"]),
        date_getter_B=lambda item: cast(datetime, item["modified"]),
    ),
    AlwaysFirstRS.name: AlwaysFirstRS(),  # type: ignore
    AlwaysSecondRS.name: AlwaysSecondRS(),  # type: ignore
}


def app_name():
    """
    Return the name of the application which defines the config, cache, and share directories
    of this app.
    """
    if "TASKWARRIOR_SYNCALL_TESTENV" in os.environ:
        return "test_taskwarrior_syncall"
    else:
        return "taskwarrior_syncall"


def get_config_name_for_args(*args) -> str:
    """
    Get a name string by concatenating the given args.

    Usage::

    >>> get_config_name_for_args("123456", None, "+remindme")
    '123456__None__+remindme'
    >>> get_config_name_for_args("123456", None, ("a_tag",))
    '123456__None__a_tag'
    >>> get_config_name_for_args("123456", None, ("a_tag", "b_tag"))
    '123456__None__a_tag,b_tag'
    >>> get_config_name_for_args("123456")
    Traceback (most recent call last):
    RuntimeError: ...
    """

    # sanity check
    if len(args) == 1:
        raise RuntimeError("get_config_name_for_args requires more > 1 arguments")

    def format_(obj: Any) -> str:
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, Iterable):
            return ",".join(map(str, obj))
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
        logger.info(f"\n\nLoading configuration - {prefs_manager.config_file}.{combination}")
        return prefs_manager[combination]


def cache_or_reuse_cached_combination(
    config_args: Mapping[str, Any],
    config_fname: str,
    custom_combination_savename: Optional[str],
):
    """
    App utility function that either retrieves the configuration for the app at hand based on
    the given arguments or retrieves it based on the custom configuartion name specified.
    """

    if custom_combination_savename is None:
        config_name = get_config_name_for_args(*config_args.values())
    else:
        config_name = custom_combination_savename

    # see if this combination corresonds to an already existing configuration -----------------
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


def report_toplevel_exception():
    logger.exception(
        "Application failed; above you can find the error message, which you can use to"
        f" create an issue -> [{ISSUES_URL}]."
    )


def inform_about_combination_name_usage(exec_name: str, combination_name: str):
    logger.success(
        'Sync completed successfully. You can now use the "-c" option to refer to this'
        " particular combination\n\n"
        f"  {exec_name} -c {combination_name}"
    )
