"""Console script for notion_taskwarrior."""
import os
import sys
from typing import List

import click
from bubop import (
    check_optional_mutually_exclusive,
    format_dict,
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
    verbosity_int_to_std_logging_lvl,
)

from syncall import inform_about_app_extras

try:
    from syncall import NotionSide, TaskWarriorSide
except ImportError:
    inform_about_app_extras(["notion", "tw"])


from notion_client import Client  # type: ignore

from syncall import (
    Aggregator,
    __version__,
    cache_or_reuse_cached_combination,
    convert_notion_to_tw,
    convert_tw_to_notion,
    fetch_app_configuration,
    fetch_from_pass_manager,
    get_resolution_strategy,
    inform_about_combination_name_usage,
    list_named_combinations,
    report_toplevel_exception,
)
from syncall.cli import (
    opt_combination,
    opt_custom_combination_savename,
    opt_list_combinations,
    opt_notion_page_id,
    opt_notion_token_pass_path,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
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
@opt_list_combinations("TW", "Notion")
@opt_custom_combination_savename("TW", "Notion")
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def main(
    notion_page_id: str,
    tw_tags: List[str],
    tw_project: str,
    token_pass_path: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_combinations: bool,
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

    if do_list_combinations:
        list_named_combinations(config_fname="tw_notion_configs")
        return 0

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)
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

    # more checks -----------------------------------------------------------------------------
    if notion_page_id is None:
        logger.error(
            "You have to provide the page ID of the Notion page for synchronization. You can"
            " do so either via CLI arguments or by specifying an existing saved combination"
        )
        sys.exit(1)

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
    sys.exit(main())
