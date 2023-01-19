"""Console script for asana_taskwarrior."""
import os
import sys
from typing import List

import asana
import click
from bubop import (
    check_optional_mutually_exclusive,
    format_dict,
    log_to_syslog,
    logger,
    loguru_tqdm_sink,
)

from syncall import inform_about_app_extras
from syncall.app_utils import error_and_exit

try:
    from syncall import AsanaSide, TaskWarriorSide
except ImportError:
    inform_about_app_extras(["asana", "tw"])


from syncall import (
    Aggregator,
    __version__,
    cache_or_reuse_cached_combination,
    convert_asana_to_tw,
    convert_tw_to_asana,
    fetch_app_configuration,
    fetch_from_pass_manager,
    get_resolution_strategy,
    inform_about_combination_name_usage,
    list_asana_workspaces,
    list_named_combinations,
    opt_asana_task_gid,
    opt_asana_token_pass_path,
    opt_asana_workspace_gid,
    opt_asana_workspace_name,
    opt_combination,
    opt_custom_combination_savename,
    opt_list_asana_workspaces,
    opt_list_combinations,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
    report_toplevel_exception,
)


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
# Asana options ------------------------------------------------------------------------------
# --asana-task-gid is used to ease development and debugging. It is not currently
# suitable for regular use.
@opt_asana_task_gid(hidden=True)
@opt_asana_token_pass_path()
@opt_asana_workspace_gid()
@opt_asana_workspace_name()
@opt_list_asana_workspaces()
# taskwarrior options -------------------------------------------------------------------------
@opt_tw_tags()
@opt_tw_project()
# misc options --------------------------------------------------------------------------------
@opt_resolution_strategy()
@opt_combination("TW", "Asana")
@opt_list_combinations("TW", "Asana")
@opt_custom_combination_savename("TW", "Asana")
@click.option("-v", "--verbose", count=True)
@click.version_option(__version__)
def main(
    asana_task_gid: str,
    asana_workspace_gid: str,
    asana_workspace_name: str,
    do_list_asana_workspaces: bool,
    tw_tags: List[str],
    tw_project: str,
    token_pass_path: str,
    resolution_strategy: str,
    verbose: int,
    combination_name: str,
    custom_combination_savename: str,
    do_list_combinations: bool,
):
    loguru_tqdm_sink(verbosity=verbose)

    log_to_syslog(name="tw_asana_sync")
    logger.debug("Initialising...")
    inform_about_config = False

    if do_list_combinations:
        list_named_combinations(config_fname="tw_asana_configs")
        return 0

    # find token to connect to asana ---------------------------------------------------------
    token = os.environ.get("ASANA_PERSONAL_ACCESS_TOKEN")
    if token is None and token_pass_path is None:
        # TODO Re-write this.
        # Hacky way of accessing the parameter naem for the token pass path.
        name = opt_asana_token_pass_path()(lambda: None).__click_params__[0].opts[-1]
        error_and_exit(
            f"You must provide an Asana Personal Access Token, using the {name} flag"
        )
    if token is not None:
        logger.debug(
            "Reading the Asana Personal Access Token (PAT) from environment variable..."
        )
    else:
        token = fetch_from_pass_manager(token_pass_path)

    # cli validation --------------------------------------------------------------------------
    check_optional_mutually_exclusive(combination_name, custom_combination_savename)
    combination_of_tw_project_tags_and_asana_workspace = any(
        [tw_project, tw_tags, asana_workspace_gid, asana_workspace_name]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_project_tags_and_asana_workspace
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            config_fname="tw_asana_configs", combination=combination_name
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        asana_workspace_gid = app_config["asana_workspace_gid"]
        if "asana_task_gid" in app_config:
            asana_task_gid = app_config["asana_task_gid"]

    # initialize asana -----------------------------------------------------------------------
    client = asana.Client.access_token(token)
    asana_disable = client.headers.get("Asana-Disable", "")
    client.headers["Asana-Disable"] = ",".join(
        [client.headers.get("Asana-Disable", ""), "new_user_task_lists"]
    )
    client.options["client_name"] = "syncall"

    # asana workspaces-------------------------------------------------------------------------
    # Validate Asana workspace selection. Skip this only if we are going to
    # --list-asana-workspaces or if --asana-task-gid was not specified.
    if asana_task_gid is None and not do_list_asana_workspaces:
        if asana_workspace_gid is None and asana_workspace_name is None:
            error_and_exit("Provide either an Asana workspace name or GID to sync.")

        if asana_workspace_gid is not None and asana_workspace_name is not None:
            error_and_exit("Provide either Asana workspace GID or name, but not both.")

        found_workspace = False

        for workspace in client.workspaces.find_all():
            if workspace["gid"] == asana_workspace_gid:
                asana_workspace_name = workspace["name"]
                found_workspace = True
                break
            if workspace["name"] == asana_workspace_name:
                if found_workspace:
                    error_and_exit(
                        "Found multiple workspaces with the provided name. Please specify"
                        " workspace GID instead."
                    )
                else:
                    asana_workspace_gid = workspace["gid"]
                    found_workspace = True

        if not found_workspace:
            if asana_workspace_gid:
                error_and_exit(
                    "No Asana workspace was found with a GID matching the one provided."
                )
            if asana_workspace_name:
                error_and_exit(
                    "No Asana workspace was found with a name matching the one provided."
                )

    # combination manually specified ----------------------------------------------------------
    if combination_name is None:
        config_args = {
            "asana_workspace_gid": asana_workspace_gid,
            "tw_project": tw_project,
            "tw_tags": tw_tags,
        }
        if asana_task_gid is not None:
            config_args["asana_task_gid"] = asana_task_gid
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args,
            config_fname="tw_asana_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # at least one of tw_tags, tw_project should be set ---------------------------------------
    if not do_list_asana_workspaces and not tw_tags and not tw_project:
        error_and_exit(
            "You have to provide at least one valid tag or a valid project ID to use for"
            " the synchronization"
        )

    # announce configuration ------------------------------------------------------------------
    announce_items = {
        "TW Tags": tw_tags,
        "TW Project": tw_project,
        "Asana Workspace GID": asana_workspace_gid,
        "Asana Workspace Name": asana_workspace_name,
    }
    if asana_task_gid is not None:
        announce_items["Asana Task GID"] = asana_task_gid
    logger.info(
        format_dict(
            header="Configuration",
            items=announce_items,
            prefix="\n\n",
            suffix="\n",
        )
    )

    # initialize taskwarrior ------------------------------------------------------------------
    tw_side = TaskWarriorSide(tags=tw_tags, project=tw_project)

    if do_list_asana_workspaces:
        list_asana_workspaces(client)
        return 0

    asana_side = AsanaSide(
        client=client, task_gid=asana_task_gid, workspace_gid=asana_workspace_gid
    )

    # sync ------------------------------------------------------------------------------------
    try:
        with Aggregator(
            side_A=asana_side,
            side_B=tw_side,
            converter_A_to_B=convert_asana_to_tw,
            converter_B_to_A=convert_tw_to_asana,
            resolution_strategy=get_resolution_strategy(
                resolution_strategy, side_A_type=type(asana_side), side_B_type=type(tw_side)
            ),
            config_fname=combination_name,
            ignore_keys=(
                (
                    "completed_at",
                    "created_at",
                    "modified_at",
                ),
                ("end", "entry", "modified", "urgency"),
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
