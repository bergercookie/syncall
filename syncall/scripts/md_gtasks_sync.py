from typing import List

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
    from syncall.google.gtasks_side import GTasksSide
    from syncall.filesystem.markdown_tasks_side import MarkdownTasksSide
except ImportError:
    inform_about_app_extras(["google", "fs"])

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
    opt_google_oauth_port,
    opt_google_secret_override,
    opt_gtasks_list,
    opts_markdown,
    opts_miscellaneous,
)
from syncall.tw_gtasks_utils import convert_gtask_to_md, convert_md_to_gtask


@click.command()
@opt_gtasks_list()
@opt_google_secret_override()
@opt_google_oauth_port()
@opts_markdown()
@opts_miscellaneous(side_A_name="Obsidian", side_B_name="Google Tasks")
def main(
    gtasks_list: str,
    google_secret: str,
    oauth_port: int,
    markdown_file: str,
    prefer_scheduled_date: bool,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    pdb_on_error: bool,
    confirm: bool,
):
    """Synchronize lists from your Google Tasks with filters from Taskwarrior.

    The list of MD tasks can be based on a Markdown file path
    while the list in GTasks should be provided by their name. if it doesn't
    exist it will be created.
    """
    # setup logger ----------------------------------------------------------------------------
    loguru_tqdm_sink(verbosity=verbose)
    app_log_to_syslog()
    logger.debug("Initialising...")
    inform_about_config = False

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)

    combination_of_file_and_gtasks_list = any(
        [
            markdown_file,
            gtasks_list,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_file_and_gtasks_list
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Obsidian", side_B_name="Google Tasks", combination=combination_name
        )
        markdown_file = app_config["markdown_file"]
        gtasks_list = app_config["gtasks_list"]

    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "gtasks_list": gtasks_list,
                "markdown_file": markdown_file,
            },
            config_fname="md_gtasks_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # more checks -----------------------------------------------------------------------------
    if gtasks_list is None:
        error_and_exit(
            "You have to provide the name of a Google Tasks list to synchronize events"
            " to/from. You can do so either via CLI arguments or by specifying an existing"
            " saved combination"
        )

    # announce configuration ------------------------------------------------------------------
    logger.info(
        format_dict(
            header="Configuration",
            items={
                "Markdown Filename Path": markdown_file,
                "Google Tasks": gtasks_list,
                "Prefer scheduled dates": prefer_scheduled_date,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    md_side = MarkdownTasksSide(
        markdown_file=markdown_file
    )

    gtasks_side = GTasksSide(
        task_list_title=gtasks_list, oauth_port=oauth_port, client_secret=google_secret
    )

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # take extra arguments into account -------------------------------------------------------
    def convert_B_to_A(*args, **kargs):
        return convert_md_to_gtask(
            *args,
            **kargs,
            set_scheduled_date=prefer_scheduled_date,
        )

    convert_B_to_A.__doc__ = convert_md_to_gtask.__doc__

    def convert_A_to_B(*args, **kargs):
        return convert_gtask_to_md(
            *args,
            **kargs,
            set_scheduled_date=prefer_scheduled_date,
        )

    convert_A_to_B.__doc__ = convert_gtask_to_md.__doc__

    # sync ------------------------------------------------------------------------------------
    with Aggregator(
        side_A=gtasks_side,
        side_B=md_side,
        converter_B_to_A=convert_B_to_A,
        converter_A_to_B=convert_A_to_B,
        resolution_strategy=get_resolution_strategy(
            resolution_strategy, side_A_type=type(gtasks_side), side_B_type=type(md_side)
        ),
        config_fname=combination_name,
        ignore_keys=(
            ("last_modified_date"),
            (),
        ),
    ) as aggregator:
        aggregator.sync()

    return 0


if __name__ == "__main__":
    main()
