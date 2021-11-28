"""Console script for notion_taskwarrior."""
import os
import subprocess
import sys
import traceback
from pathlib import Path
from typing import List

import click
from bubop import (
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
    non_empty,
    read_gpg_token,
    valid_path,
    verbosity_int_to_std_logging_lvl,
)

try:
    from taskwarrior_syncall import NotionSide
except ImportError:
    logger.error(f"You have to install the [notion] extra for {sys.argv[0]} to work. Exiting.")
    sys.exit(1)


from notion_client import Client  # type: ignore

from taskwarrior_syncall import (
    Aggregator,
    TaskWarriorSide,
    convert_notion_to_tw,
    convert_tw_to_notion,
    name_to_resolution_strategy,
)


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
@click.option(
    "-n",
    "--notion-page",
    "notion_page_id",
    required=True,
    type=str,
    help="Page ID of the Notion page to sync",
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
@click.option(
    "--token",
    "--token-pass-path",
    "token_pass_path",
    help="Path in the UNIX password manager to fetch",
    default="notion.so/dev/integration/taskwarrior/token",
)
# misc options --------------------------------------------------------------------------------
@click.option(
    "-r",
    "--resolution_strategy",
    default="AlwaysSecondRS",
    type=click.Choice(list(name_to_resolution_strategy.keys())),
    help="Resolution strategy to use during conflicts",
)
@click.option("-v", "--verbose", count=True)
def main(
    notion_page_id: str,
    tw_tags: List[str],
    tw_project: str,
    token_pass_path: str,
    resolution_strategy: str,
    verbose: int,
):
    """Synchronise a list of TW tasks with a Notion page.

    The list of TW tasks is given by a
    user filter while the notion page should be provided by the url
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="tw_notion_sync")
    logger.debug("Initialising...")

    # find token to connect to notion ---------------------------------------------------------
    token_v2 = os.environ.get("NOTION_API_KEY")
    if token_v2 is not None:
        logger.debug("Reading the Notion API key from environment variable...")
    else:
        logger.debug("Attempting to read the Notion API key from UNIX Password Store...")
        pass_dir = valid_path(os.environ.get("PASSWORD_STORE_DIR", "~/.password-store"))
        if str(token_pass_path).startswith(str(pass_dir)):
            path = Path(token_pass_path)
        else:
            path = pass_dir / token_pass_path
        pass_full_path = path.with_suffix(".gpg")

        try:
            token_v2 = read_gpg_token(pass_full_path)
        except subprocess.CalledProcessError as err:
            logger.exception(
                "".join(
                    [
                        "Couldn't read the notion token from pass\nFull path ->"
                        f" {pass_full_path}",
                        non_empty("Stdout", err.stdout),
                        non_empty("Stderr", err.stderr),
                    ]
                )
            )
            return 1

    assert token_v2

    # initialize taskwarrior -------------------------------------------------------------
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    # initialize notion -----------------------------------------------------------------------
    # client is a bit too verbose by default.
    client_verbosity = max(verbose - 1, 0)
    client = Client(
        auth=token_v2, log_level=verbosity_int_to_std_logging_lvl(client_verbosity)
    )
    notion_side = NotionSide(client=client, page_id=notion_page_id)

    try:
        with Aggregator(
            side_A=notion_side,
            side_B=tw_side,
            converter_B_to_A=convert_tw_to_notion,
            converter_A_to_B=convert_notion_to_tw,
            resolution_strategy=name_to_resolution_strategy[resolution_strategy],
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
