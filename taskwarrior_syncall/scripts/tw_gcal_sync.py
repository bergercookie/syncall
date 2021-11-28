import sys
import traceback

import click
from bubop import log_to_syslog, logger, loguru_tqdm_sink

try:
    from taskwarrior_syncall import GCalSide
except ImportError:
    logger.error(f"You have to install the [gcal] extra for {sys.argv[0]} to work. Exiting.")
    sys.exit(1)

from taskwarrior_syncall import (
    Aggregator,
    TaskWarriorSide,
    convert_gcal_to_tw,
    convert_tw_to_gcal,
    name_to_resolution_strategy,
)


@click.command()
# google calendar options ---------------------------------------------------------------------
@click.option(
    "-c",
    "--gcal-calendar",
    required=True,
    type=str,
    help="Name of the Google Calendar to sync (will be created if not there)",
)
@click.option(
    "--gcal-secret",
    required=False,
    default=None,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="Override the client secret used for the communication with the Google Calendar API",
)
@click.option(
    "--oauth-port",
    default=8081,
    type=int,
    help="Port to use for OAuth Authentication with Google Calendar",
)
# taskwarrior options -------------------------------------------------------------------------
@click.option(
    "-t",
    "--taskwarrior-tags",
    "tw_tags",
    required=False,
    type=str,
    help="Taskwarrior tags to sync",
    multiple=True,
)
@click.option(
    "-p",
    "--tw-project",
    "tw_project",
    required=False,
    type=str,
    help="Taskwarrior project to sync",
)
# misc options --------------------------------------------------------------------------------
@click.option(
    "-r",
    "--resolution_strategy",
    "resolution_strategy_name",
    default="AlwaysSecondRS",
    type=click.Choice(list(name_to_resolution_strategy.keys())),
    help="Resolution strategy to use during conflicts",
)
@click.option("-v", "--verbose", count=True)
def main(
    gcal_calendar,
    gcal_secret,
    tw_tags,
    tw_project,
    oauth_port,
    resolution_strategy_name,
    verbose,
):
    """Synchronize a calendar from your Google Calendar with a tag from Taskwarrior."""
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="tw_gcal_sync")
    logger.debug("Initialising...")

    # Either tags or project should be non-empty ------------------------------------------
    if not tw_tags and not tw_project:
        raise RuntimeError(
            "You have to provide at least one valid tag or a valid project ID to use for"
            " the synchronization"
        )

    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    gcal_side = GCalSide(
        calendar_summary=gcal_calendar, oauth_port=oauth_port, client_secret=gcal_secret
    )

    logger.info(
        "\n\nSynchronizing:\n\n"
        f"\t* [gcal] calendar:{gcal_calendar}\n"
        f"\t* [tw] tags: {tw_tags}, project: {tw_project}\n"
    )
    try:
        with Aggregator(
            side_A=gcal_side,
            side_B=tw_side,
            converter_B_to_A=convert_tw_to_gcal,
            converter_A_to_B=convert_gcal_to_tw,
            resolution_strategy=name_to_resolution_strategy[resolution_strategy_name],
        ) as aggregator:
            aggregator.sync()
    except KeyboardInterrupt:
        logger.info("Exiting...")
    except:
        logger.info(traceback.format_exc())
        logger.error(
            "Application failed; above you can find the error message, which you can use to"
            " create an issue at https://github.com/bergercookie/taskwarrior_syncall/issues."
        )


if __name__ == "__main__":
    main()
