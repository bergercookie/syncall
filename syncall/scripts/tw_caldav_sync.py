import os
import subprocess
from typing import List, Optional

import caldav
import click
from bubop import (
    check_optional_mutually_exclusive,
    check_required_mutually_exclusive,
    format_dict,
    logger,
    loguru_tqdm_sink,
)

from syncall.app_utils import confirm_before_proceeding, inform_about_app_extras

try:
    from syncall.caldav.caldav_side import CaldavSide
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["caldav", "tw"])

from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_log_to_syslog,
    cache_or_reuse_cached_combination,
    error_and_exit,
    fetch_app_configuration,
    fetch_from_pass_manager,
    get_resolution_strategy,
    register_teardown_handler,
)
from syncall.cli import opts_caldav, opts_miscellaneous, opts_tw_filtering
from syncall.tw_caldav_utils import convert_caldav_to_tw, convert_tw_to_caldav


@click.command()
@opts_caldav()
@opts_tw_filtering()
@opts_miscellaneous("TW", "Caldav")
def main(
    caldav_calendar: str,
    caldav_url: str,
    caldav_user: Optional[str],
    caldav_passwd_pass_path: str,
    caldav_passwd_cmd: str,
    tw_filter: str,
    tw_tags: List[str],
    tw_project: str,
    tw_only_modified_last_X_days: str,
    tw_sync_all_tasks: bool,
    prefer_scheduled_date: bool,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    pdb_on_error: bool,
    confirm: bool,
):
    """Synchronize lists of tasks from your caldav Calendar with filters from Taskwarrior.

    The list of TW tasks is determined by a combination of TW tags and a TW project. Use
    `--all` to synchronize all tasks.

    The calendar in Caldav should be provided by their name. If it doesn't exist it will be
    created.
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    app_log_to_syslog()
    logger.debug("Initialising...")
    inform_about_config = False

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)

    tw_filter_li = [
        t
        for t in [
            tw_filter,
            tw_only_modified_last_X_days,
        ]
        if t
    ]

    combination_of_tw_filters_and_caldav_calendar = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            caldav_calendar,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_filters_and_caldav_calendar
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Taskwarrior", side_B_name="Caldav", combination=combination_name
        )
        tw_filter_li = app_config["tw_filter_li"]
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        caldav_calendar = app_config["caldav_calendar"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "caldav_calendar": caldav_calendar,
                "tw_filter_li": tw_filter_li,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_caldav_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # more checks -----------------------------------------------------------------------------
    combination_of_tw_related_options = any([tw_filter_li, tw_tags, tw_project])
    check_required_mutually_exclusive(
        tw_sync_all_tasks,
        combination_of_tw_related_options,
        "sync_all_tw_tasks",
        "combination of specific TW-related options",
    )

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "TW Filter": " ".join(tw_filter_li),
                "TW Tags": tw_tags,
                "TW Project": tw_project,
                "TW Sync All Tasks": tw_sync_all_tasks,
                "Caldav Calendar": caldav_calendar,
                "Prefer scheduled dates": prefer_scheduled_date,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    # tw
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li), tags=tw_tags, project=tw_project
    )

    # caldav
    if not caldav_url or not caldav_calendar:
        logger.debug(caldav_url)
        logger.debug(caldav_calendar)
        error_and_exit(
            "You must provide a URL and calendar in order to synchronize via caldav"
        )

    # fetch username
    if not caldav_user:
        caldav_user = os.environ.get("CALDAV_USERNAME")
    if caldav_user is None:
        error_and_exit(
            "You must provide a username in order to synchronize via caldav, either "
        )

    # fetch password
    caldav_passwd = os.environ.get("CALDAV_PASSWD")
    if caldav_passwd is not None:
        logger.debug("Reading the caldav password from environment variable...")
    elif caldav_passwd_cmd is not None:
        proc = subprocess.run(caldav_passwd_cmd, shell=True, text=True, capture_output=True)
        if proc.returncode != 0:
            error_and_exit(f"Password command failed: {proc.stderr}")

        caldav_passwd = proc.stdout.rstrip()
    else:
        caldav_passwd = fetch_from_pass_manager(caldav_passwd_pass_path)

    client = caldav.DAVClient(url=caldav_url, username=caldav_user, password=caldav_passwd)
    caldav_side = CaldavSide(client=client, calendar_name=caldav_calendar)

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=caldav_side,
        side_B=tw_side,
        converter_B_to_A=convert_tw_to_caldav,
        converter_A_to_B=convert_caldav_to_tw,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy, side_A_type=type(caldav_side), side_B_type=type(tw_side)
        ),
        config_fname=combination_name,
        ignore_keys=(
            (),
            (),
        ),
        catch_exceptions=not pdb_on_error,
    ) as aggregator:
        aggregator.sync()

    return 0


if __name__ == "__main__":
    main()
