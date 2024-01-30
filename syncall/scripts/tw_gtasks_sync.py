from typing import List

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
    from syncall.google.gtasks_side import GTasksSide
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["google", "tw"])

from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_log_to_syslog,
    cache_or_reuse_cached_combination,
    error_and_exit,
    fetch_app_configuration,
    get_resolution_strategy,
    register_teardown_handler,
)
from syncall.cli import (
    opt_google_oauth_port,
    opt_google_secret_override,
    opt_gtasks_list,
    opts_miscellaneous,
    opts_tw_filtering,
)
from syncall.tw_gtasks_utils import convert_gtask_to_tw, convert_tw_to_gtask


@click.command()
@opt_gtasks_list()
@opt_google_secret_override()
@opt_google_oauth_port()
@opts_tw_filtering()
@opts_miscellaneous(side_A_name="TW", side_B_name="Google Tasks")
def main(
    gtasks_list: str,
    google_secret: str,
    oauth_port: int,
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
    """Synchronize lists from your Google Tasks with filters from Taskwarrior.

    The list of TW tasks can be based on a TW project, tag, on the modification date or on an
    arbitrary filter while the list in GTasks should be provided by their name. if it doesn't
    exist it will be created.
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

    combination_of_tw_filters_and_gtasks_list = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            gtasks_list,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_filters_and_gtasks_list
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="TW", side_B_name="Google Tasks", combination=combination_name
        )
        tw_filter_li = app_config["tw_filter_li"]
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        gtasks_list = app_config["gtasks_list"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "gtasks_list": gtasks_list,
                "tw_filter_li": tw_filter_li,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_gtasks_configs",
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

    if gtasks_list is None:
        error_and_exit(
            "You have to provide the name of a Google Tasks list to synchronize events"
            " to/from. You can do so either via CLI arguments or by specifying an existing"
            " saved combination"
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
                "Google Tasks": gtasks_list,
                "Prefer scheduled dates": prefer_scheduled_date,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    # NOTE: We don't explicitly pass the tw_sync_all_tasks boolean. However we implicitly do by
    # verifying beforehand that if this flag is specified the user cannot specify any of the
    # other `tw_filter_li`, `tw_tags`, `tw_project` options.
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li), tags=tw_tags, project=tw_project
    )

    gtasks_side = GTasksSide(
        task_list_title=gtasks_list, oauth_port=oauth_port, client_secret=google_secret
    )

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # take extra arguments into account -------------------------------------------------------
    def convert_B_to_A(*args, **kargs):
        return convert_tw_to_gtask(
            *args,
            **kargs,
        )

    convert_B_to_A.__doc__ = convert_tw_to_gtask.__doc__

    def convert_A_to_B(*args, **kargs):
        return convert_gtask_to_tw(
            *args,
            **kargs,
            set_scheduled_date=prefer_scheduled_date,
        )

    convert_A_to_B.__doc__ = convert_gtask_to_tw.__doc__

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=gtasks_side,
        side_B=tw_side,
        converter_B_to_A=convert_B_to_A,
        converter_A_to_B=convert_A_to_B,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy, side_A_type=type(gtasks_side), side_B_type=type(tw_side)
        ),
        config_fname=combination_name,
        ignore_keys=(
            (),
            (),
        ),
    ) as aggregator:
        aggregator.sync()

    return 0


if __name__ == "__main__":
    main()
