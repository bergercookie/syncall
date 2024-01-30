import os
import sys
from typing import List

import click
from bubop import (
    check_optional_mutually_exclusive,
    check_required_mutually_exclusive,
    format_dict,
    logger,
    loguru_tqdm_sink,
    verbosity_int_to_std_logging_lvl,
)

from syncall.app_utils import (
    confirm_before_proceeding,
    fetch_from_pass_manager,
    inform_about_app_extras,
)

try:
    from syncall.notion.notion_side import NotionSide
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["notion", "tw"])

from notion_client import Client  # type: ignore

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
    opt_notion_page_id,
    opt_notion_token_pass_path,
    opts_miscellaneous,
    opts_tw_filtering,
)
from syncall.tw_notion_utils import convert_notion_to_tw, convert_tw_to_notion


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
@opt_notion_page_id()
@opt_notion_token_pass_path()
@opts_tw_filtering()
@opts_miscellaneous("TW", "Notion")
def main(
    notion_page_id: str,
    token_pass_path: str,
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
    """Synchronise filters of TW tasks with the to_do items of Notion pages.

    The list of TW tasks can be based on a TW project, tag, on the modification date or on an
    arbitrary filter  while the notion pages should be provided by their URLs.
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

    combination_of_tw_filters_and_notion_page = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            notion_page_id,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_filters_and_notion_page
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Taskwarrior", side_B_name="Notion", combination=combination_name
        )
        tw_filter_li = app_config["tw_filter_li"]
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        notion_page_id = app_config["notion_page_id"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "notion_page_id": notion_page_id,
                "tw_filter_li": tw_filter_li,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
            },
            config_fname="tw_notion_configs",
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

    if notion_page_id is None:
        error_and_exit(
            "You have to provide the page ID of the Notion page for synchronization. You can"
            " do so either via CLI arguments or by specifying an existing saved combination"
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
                "Notion Page ID": notion_page_id,
                "Prefer scheduled dates": prefer_scheduled_date,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # find token to connect to notion ---------------------------------------------------------
    api_key_env_var = "NOTION_API_KEY"
    token_v2 = os.environ.get(api_key_env_var)
    if token_v2 is not None:
        logger.debug("Reading the Notion API key from environment variable...")
    else:
        if token_pass_path is None:
            logger.error(
                "You have to provide the Notion API key, either via the"
                f" {api_key_env_var} environment variable or via the UNIX Passowrdr Manager"
                ' and the "--token-pass-path" CLI parameter'
            )
            sys.exit(1)
        token_v2 = fetch_from_pass_manager(token_pass_path)

    assert token_v2

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # initialize sides ------------------------------------------------------------------------
    # tw
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li), tags=tw_tags, project=tw_project
    )

    # notion
    # client is a bit too verbose by default.
    client_verbosity = max(verbose - 1, 0)
    client = Client(
        auth=token_v2, log_level=verbosity_int_to_std_logging_lvl(client_verbosity)
    )
    notion_side = NotionSide(client=client, page_id=notion_page_id)

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=notion_side,
        side_B=tw_side,
        converter_B_to_A=convert_tw_to_notion,
        converter_A_to_B=convert_notion_to_tw,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy, side_A_type=type(notion_side), side_B_type=type(tw_side)
        ),
        config_fname=combination_name,
        ignore_keys=(
            ("last_modified_date",),
            ("due", "end", "entry", "modified", "urgency"),
        ),
    ) as aggregator:
        aggregator.sync()

    return 0


if __name__ == "__main__":
    sys.exit(main())
