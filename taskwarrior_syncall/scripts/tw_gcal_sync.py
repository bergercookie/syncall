from typing import List

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
    from taskwarrior_syncall import GCalSide
except ImportError:
    inform_about_app_extras(["google"])

from taskwarrior_syncall import (
    Aggregator,
    TaskWarriorSide,
    __version__,
    cache_or_reuse_cached_combination,
    convert_gcal_to_tw,
    convert_tw_to_gcal,
    fetch_app_configuration,
    get_resolution_strategy,
    inform_about_combination_name_usage,
    list_named_combinations,
    opt_combination,
    opt_custom_combination_savename,
    opt_gcal_calendar,
    opt_google_oauth_port,
    opt_google_secret_override,
    opt_list_combinations,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
    report_toplevel_exception,
)


@click.command()
# google calendar options ---------------------------------------------------------------------
@opt_gcal_calendar()
@opt_google_secret_override()
@opt_google_oauth_port()
# taskwarrior options -------------------------------------------------------------------------
@opt_tw_tags()
@opt_tw_project()
# misc options --------------------------------------------------------------------------------
@opt_list_combinations("TW", "Google Calendar")
@opt_resolution_strategy()
@opt_combination("TW", "Google Calendar")
@opt_custom_combination_savename("TW", "Google Calendar")
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def main(
    gcal_calendar: str,
    google_secret: str,
    oauth_port: int,
    tw_tags: List[str],
    tw_project: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_combinations: bool,
):
    """Synchronize calendars from your Google Calendar with filters from Taskwarrior.

    The list of TW tasks is determined by a combination of TW tags and a TW project while the
    calendar in GCal should be provided by their name. if it doesn't exist it will be crated
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="tw_gcal_sync")
    logger.debug("Initialising...")
    inform_about_config = False

    if do_list_combinations:
        list_named_combinations(config_fname="tw_gcal_configs")
        return 0

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)
    combination_of_tw_project_tags_and_gcal_calendar = any(
        [
            tw_project,
            tw_tags,
            gcal_calendar,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_project_tags_and_gcal_calendar
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            config_fname="tw_gcal_configs", combination=combination_name
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        gcal_calendar = app_config["gcal_calendar"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "gcal_calendar": gcal_calendar,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_gcal_configs",
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
                "Google Calendar": gcal_calendar,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )

    # initialize sides ------------------------------------------------------------------------
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    gcal_side = GCalSide(
        calendar_summary=gcal_calendar, oauth_port=oauth_port, client_secret=google_secret
    )

    # sync ------------------------------------------------------------------------------------
    try:
        with Aggregator(
            side_A=gcal_side,
            side_B=tw_side,
            converter_B_to_A=convert_tw_to_gcal,
            converter_A_to_B=convert_gcal_to_tw,
            resolution_strategy=get_resolution_strategy(
                resolution_strategy, side_A_type=type(gcal_side), side_B_type=type(tw_side)
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
