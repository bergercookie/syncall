import sys
from typing import Sequence

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
    from syncall.google.gkeep_todo_side import GKeepTodoSide
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["gkeep", "tw"])

from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_log_to_syslog,
    cache_or_reuse_cached_combination,
    fetch_app_configuration,
    get_resolution_strategy,
    gkeep_read_username_password_token,
    inform_about_combination_name_usage,
    register_teardown_handler,
    write_to_pass_manager,
)
from syncall.cli import opt_gkeep_note, opts_gkeep, opts_miscellaneous, opts_tw_filtering
from syncall.tw_gkeep_utils import convert_gkeep_todo_to_tw, convert_tw_to_gkeep_todo


@click.command()
@opts_gkeep()
@opt_gkeep_note()
@opts_tw_filtering()
@opts_miscellaneous(side_A_name="TW", side_B_name="Google Keep")
def main(
    gkeep_note: str,
    gkeep_user_pass_path: str,
    gkeep_passwd_pass_path: str,
    gkeep_token_pass_path: str,
    tw_filter: str,
    tw_tags: Sequence[str],
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
    """Synchronize Notes from your Google Keep with filters from Taskwarrior.

    The list of TW tasks is determined by a combination of TW tags and a TW project while the
    note in GKeep should be specified using their full name. if it doesn't exist it will be
    created.

    This service will create TaskWarrior tasks with the specified filter for each one of the
    checkboxed items in the specified Google Keep note and will create Google Keep items for
    each one of the tasks in the Taskwarrior filter. You have to first "Show checkboxes" in the
    Google Keep Note in order to use it with this service.
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

    combination_of_tw_filters_and_gkeep_note = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            gkeep_note,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_filters_and_gkeep_note
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Taskwarrior", side_B_name="Google Keep", combination=combination_name
        )
        tw_filter_li = app_config["tw_filter_li"]
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        gkeep_note = app_config["gkeep_note"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "gkeep_note": gkeep_note,
                "tw_filter_li": tw_filter_li,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_gkeep_configs",
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

    if gkeep_note is None:
        logger.error(
            "You have to provide the name of a Google Keep note to synchronize items"
            " to/from. You can do so either via CLI arguments or by specifying an existing"
            " saved combination"
        )
        sys.exit(1)

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "TW Filter": " ".join(tw_filter_li),
                "TW Tags": tw_tags,
                "TW Project": tw_project,
                "TW Sync All Tasks": tw_sync_all_tasks,
                "Google Keep Note": gkeep_note,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    gkeep_user, gkeep_passwd, gkeep_token = gkeep_read_username_password_token(
        gkeep_user_pass_path,
        gkeep_passwd_pass_path,
        gkeep_token_pass_path,
    )

    # initialize google keep  -----------------------------------------------------------------
    gkeep_side = GKeepTodoSide(
        note_title=gkeep_note,
        gkeep_user=gkeep_user,
        gkeep_passwd=gkeep_passwd,
        gkeep_token=gkeep_token,
        notes_label="tw_gkeep_sync",
    )

    # initialize taskwarrior ------------------------------------------------------------------
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li), tags=tw_tags, project=tw_project
    )

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=gkeep_side,
        side_B=tw_side,
        converter_B_to_A=convert_tw_to_gkeep_todo,
        converter_A_to_B=convert_gkeep_todo_to_tw,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy, side_A_type=type(gkeep_side), side_B_type=type(tw_side)
        ),
        config_fname=combination_name,
        ignore_keys=(
            (),
            ("due", "end", "entry", "modified", "urgency"),
        ),
    ) as aggregator:
        aggregator.sync()

    # cache the token -------------------------------------------------------------------------
    token = gkeep_side.get_master_token()
    if token is not None:
        logger.debug(f"Caching the gkeep token in pass -> {gkeep_token_pass_path}...")
        write_to_pass_manager(password_path=gkeep_token_pass_path, passwd=token)

    if inform_about_config:
        inform_about_combination_name_usage(combination_name)

    return 0


if __name__ == "__main__":
    main()
