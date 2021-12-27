"""Console script for notion_taskwarrior."""
import os
import subprocess
import sys
from pathlib import Path
from typing import List

import click
from bubop import (
    check_optional_mutually_exclusive,
    check_required_mutually_exclusive,
    format_dict,
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
    cache_or_reuse_cached_combination,
    convert_notion_to_tw,
    convert_tw_to_notion,
    fetch_app_configuration,
    inform_about_combination_name_usage,
    list_named_combinations,
    name_to_resolution_strategy,
    opt_combination,
    opt_custom_combination_savename,
    opt_list_configs,
    opt_notion_page_id,
    opt_notion_token_pass_path,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
    report_toplevel_exception,
)


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
# Notion options ------------------------------------------------------------------------------
@opt_notion_page_id()
@opt_notion_token_pass_path()
# taskwarrior options -------------------------------------------------------------------------
@opt_tw_tags()
@opt_tw_project()
# misc options --------------------------------------------------------------------------------
@opt_resolution_strategy()
@opt_combination("TW", "Notion")
@opt_list_configs("TW", "Notion")
@opt_custom_combination_savename("TW", "Notion")
@click.option("-v", "--verbose", count=True)
def main(
    notion_page_id: str,
    tw_tags: List[str],
    tw_project: str,
    token_pass_path: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_configs: bool,
):
    """Synchronise filters of TW tasks with the to_do items of Notion pages

    The list of TW tasks is determined by a combination of TW tags and TW project while the
    notion pages should be provided by their URLs.
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    log_to_syslog(name="tw_notion_sync")
    logger.debug("Initialising...")
    inform_about_config = False
    exec_name = Path(sys.argv[0]).stem

    if do_list_configs:
        list_named_combinations(config_fname="tw_notion_configs")
        return 0

    # cli validation --------------------------------------------------------------------------
    check_required_mutually_exclusive(combination_name, custom_combination_savename)
    combination_of_tw_project_tags_and_notion_page = any(
        [
            tw_project,
            tw_tags,
            notion_page_id,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_project_tags_and_notion_page
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            config_fname="tw_notion_configs", combination=combination_name
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        notion_page_id = app_config["notion_page_id"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "notion_page_id": notion_page_id,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_notion_configs",
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
                "Notion Page ID": notion_page_id,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )

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

    # initialize taskwarrior ------------------------------------------------------------------
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    # initialize notion -----------------------------------------------------------------------
    # client is a bit too verbose by default.
    client_verbosity = max(verbose - 1, 0)
    client = Client(
        auth=token_v2, log_level=verbosity_int_to_std_logging_lvl(client_verbosity)
    )
    notion_side = NotionSide(client=client, page_id=notion_page_id)

    # sync ------------------------------------------------------------------------------------
    try:
        with Aggregator(
            side_A=notion_side,
            side_B=tw_side,
            converter_B_to_A=convert_tw_to_notion,
            converter_A_to_B=convert_notion_to_tw,
            resolution_strategy=name_to_resolution_strategy[resolution_strategy],
            config_fname=combination_name,
            ignore_keys=(
                ("last_modified_date",),
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
    sys.exit(main())
