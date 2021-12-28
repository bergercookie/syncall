import sys
from pathlib import Path
from typing import List

import click
from bubop import (
    check_optional_mutually_exclusive,
    format_dict,
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
)

try:
    from taskwarrior_syncall import GKeepTodoSide
except ImportError:
    logger.error(f"You have to install the [google] extra for {sys.argv[0]} to work. Exiting.")
    sys.exit(1)

from taskwarrior_syncall import (
    Aggregator,
    TaskWarriorSide,
    cache_or_reuse_cached_combination,
    convert_gkeep_todo_to_tw,
    convert_tw_to_gkeep_todo,
    fetch_app_configuration,
    inform_about_combination_name_usage,
    list_named_combinations,
    name_to_resolution_strategy,
    opt_combination,
    opt_custom_combination_savename,
    opt_gkeep_note,
    opt_list_configs,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
    report_toplevel_exception,
)


@click.command()
# google calendar options ---------------------------------------------------------------------
@opt_gkeep_note()
# taskwarrior options -------------------------------------------------------------------------
@opt_tw_tags()
@opt_tw_project()
# misc options --------------------------------------------------------------------------------
@opt_list_configs("TW", "Google Keep")
@opt_resolution_strategy()
@opt_combination("TW", "Google Keep")
@opt_list_configs("TW", "Google Keep")
@opt_custom_combination_savename("TW", "Google Keep")
@click.option("-v", "--verbose", count=True)
def main(
    gkeep_note: str,
    tw_tags: List[str],
    tw_project: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_configs: bool,
):
    """Synchronize Notes from your Google Keep with filters from Taskwarrior.

    The list of TW tasks is determined by a combination of TW tags and a TW project while the
    note in GKeep should be provided by their name. if it doesn't exist it will be crated
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="tw_gkeep_sync")
    logger.debug("Initialising...")
    inform_about_config = False
    exec_name = Path(sys.argv[0]).stem

    if do_list_configs:
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
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    gkeep_side = GKeepTodoSide()

    # sync ------------------------------------------------------------------------------------
    try:
        with Aggregator(
            side_A=gkeep_side,
            side_B=tw_side,
            converter_B_to_A=convert_tw_to_gkeep_todo,
            converter_A_to_B=convert_gkeep_todo_to_tw,
            resolution_strategy=name_to_resolution_strategy[resolution_strategy],
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
        report_toplevel_exception()
        return 1

    if inform_about_config:
        inform_about_combination_name_usage(exec_name, combination_name)

    return 0


if __name__ == "__main__":
    main()
