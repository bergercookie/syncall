import os
from typing import Sequence

import click
from bubop import (
    check_optional_mutually_exclusive,
    format_dict,
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
)

from taskwarrior_syncall import inform_about_app_extras

try:
    from taskwarrior_syncall import GKeepTodoSide
except ImportError:
    inform_about_app_extras(["gkeepapi"])

from taskwarrior_syncall import (
    Aggregator,
    TaskWarriorSide,
    __version__,
    cache_or_reuse_cached_combination,
    convert_gkeep_todo_to_tw,
    convert_tw_to_gkeep_todo,
    fetch_app_configuration,
    fetch_from_pass_manager,
    get_resolution_strategy,
    inform_about_combination_name_usage,
    list_named_combinations,
    opt_combination,
    opt_custom_combination_savename,
    opt_gkeep_note,
    opt_gkeep_passwd_pass_path,
    opt_gkeep_user_pass_path,
    opt_list_combinations,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
    report_toplevel_exception,
)


@click.command()
# google keep options ---------------------------------------------------------------------
@opt_gkeep_note()
@opt_gkeep_user_pass_path()
@opt_gkeep_passwd_pass_path()
# taskwarrior options -------------------------------------------------------------------------
@opt_tw_tags()
@opt_tw_project()
# misc options --------------------------------------------------------------------------------
@opt_list_combinations("TW", "Google Keep")
@opt_resolution_strategy()
@opt_combination("TW", "Google Keep")
@opt_custom_combination_savename("TW", "Google Keep")
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def main(
    gkeep_note: str,
    gkeep_user_pass_path: str,
    gkeep_passwd_pass_path: str,
    tw_tags: Sequence[str],
    tw_project: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_combinations: bool,
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
    log_to_syslog(name="tw_gkeep_sync")
    logger.debug("Initialising...")
    inform_about_config = False

    if do_list_combinations:
        list_named_combinations(config_fname="tw_gkeep_configs")
        return 0

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)
    combination_of_tw_project_tags_and_gkeep_note = any(
        [
            tw_project,
            tw_tags,
            gkeep_note,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_project_tags_and_gkeep_note
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            config_fname="tw_gkeep_configs", combination=combination_name
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        gkeep_note = app_config["gkeep_note"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "gkeep_note": gkeep_note,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_gkeep_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # at least one of tw_tags, tw_project should be set ---------------------------------------
    if not tw_tags and not tw_project:
        raise RuntimeError(
            "You have to provide at least one valid tag or a valid project ID to use for"
            " the synchronization"
        )

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "TW Tags": tw_tags,
                "TW Project": tw_project,
                "Google Keep Note": gkeep_note,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )

    # initialize sides ------------------------------------------------------------------------
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

    gkeep_side = GKeepTodoSide(
        note_title=gkeep_note,
        gkeep_user=gkeep_user,
        gkeep_passwd=gkeep_passwd,
        notes_label="tw_gkeep_sync",
    )

    # initialize taskwarrior ------------------------------------------------------------------
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    # sync ------------------------------------------------------------------------------------
    try:
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
    except KeyboardInterrupt:
        logger.error("Exiting...")
        return 1
    except:
        report_toplevel_exception(is_verbose=verbose >= 1)
        return 1

    if inform_about_config:
        inform_about_combination_name_usage(combination_name)

    return 0


if __name__ == "__main__":
    main()
