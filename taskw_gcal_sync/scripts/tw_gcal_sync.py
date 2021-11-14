import traceback

import click

from taskw_gcal_sync.logger import logger, setup_logger
from taskw_gcal_sync.TWGCalAggregator import TWGCalAggregator


@click.command()
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
    "-t",
    "--taskwarrior-tag",
    "tw_tags",
    required=True,
    type=str,
    help="Taskwarrior tags to sync",
    multiple=True,
)
@click.option(
    "--oauth-port",
    default=8081,
    type=int,
    help="Port to use for oAuth Authentication with Google Calendar",
)
@click.option("-v", "--verbose", count=True, default=0)
def main(gcal_calendar, gcal_secret, tw_tags, verbose, oauth_port):
    """Main."""
    setup_logger(verbosity=verbose)
    if len(tw_tags) != 1:
        raise RuntimeError("Trying with multiple tags hasn't been tested yet. Exiting...")

    logger.info("Initialising...")
    tw_config = {"tags": list(tw_tags)}

    gcal_config = {"calendar_summary": gcal_calendar, "oauth_port": oauth_port}
    if gcal_secret:
        gcal_config["client_secret"] = gcal_secret

    try:
        with TWGCalAggregator(tw_config=tw_config, gcal_config=gcal_config) as aggregator:
            aggregator.sync()

    except KeyboardInterrupt:
        logger.info("Exiting...")
    except:
        logger.info(traceback.format_exc())
        logger.error(
            "Application failed; above you can find the error message, which you can use to"
            " create an issue at https://github.com/bergercookie/taskw_gcal_sync/issues."
        )


if __name__ == "__main__":
    main()
