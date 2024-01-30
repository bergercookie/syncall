import sys
from typing import List

import asana
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
    from syncall.asana.asana_side import AsanaSide
    from syncall.asana.utils import list_asana_workspaces
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
except ImportError:
    inform_about_app_extras(["asana", "tw"])


from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_log_to_syslog,
    cache_or_reuse_cached_combination,
    error_and_exit,
    fetch_app_configuration,
    get_resolution_strategy,
    register_teardown_handler,
)
from syncall.cli import opts_asana, opts_miscellaneous, opts_tw_filtering
from syncall.tw_asana_utils import convert_asana_to_tw, convert_tw_to_asana


# CLI parsing ---------------------------------------------------------------------------------
@click.command()
@opts_asana(hidden_gid=False)
@opts_tw_filtering()
@opts_miscellaneous("TW", "Asana")
def main(
    asana_task_gid: str,
    asana_token: str,
    asana_workspace_gid: str,
    asana_workspace_name: str,
    do_list_asana_workspaces: bool,
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
    """Synchronize your tasks in Asana with filters from Taskwarrior."""
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

    combination_of_tw_filters_and_asana_workspace = any(
        [
            tw_filter_li,
            tw_tags,
            tw_project,
            tw_sync_all_tasks,
            asana_workspace_gid,
            asana_workspace_name,
        ]
    )
    check_optional_mutually_exclusive(
        combination_name, combination_of_tw_filters_and_asana_workspace
    )

    # existing combination name is provided ---------------------------------------------------
    if combination_name is not None:
        app_config = fetch_app_configuration(
            side_A_name="Taskwarrior", side_B_name="Asana", combination=combination_name
        )
        tw_tags = app_config["tw_tags"]
        tw_project = app_config["tw_project"]
        tw_sync_all_tasks = app_config["tw_sync_all_tasks"]
        asana_workspace_gid = app_config["asana_workspace_gid"]
        asana_task_gid = app_config["asana_task_gid"]
    # combination manually specified ----------------------------------------------------------
    else:
        inform_about_config = True
        combination_name = cache_or_reuse_cached_combination(
            config_args={
                "asana_workspace_gid": asana_workspace_gid,
                "tw_project": tw_project,
                "tw_tags": tw_tags,
                "asana_task_gid": asana_task_gid,
            },
            config_fname="tw_asana_configs",
            custom_combination_savename=custom_combination_savename,
        )

    # initialize asana -----------------------------------------------------------------------
    asana_client = asana.Client.access_token(asana_token)
    asana_disable = asana_client.headers.get("Asana-Disable", "")
    asana_client.headers["Asana-Disable"] = ",".join(
        [
            asana_client.headers.get("Asana-Disable", ""),
            "new_user_task_lists",
            "new_goal_memberships",
        ]
    )
    asana_client.options["client_name"] = "syncall"

    # list workspaces and exit
    if do_list_asana_workspaces:
        list_asana_workspaces(asana_client)
        return 0

    # asana workspaces-------------------------------------------------------------------------
    # Validate Asana workspace selection. Skip this only if we are going to
    # --list-asana-workspaces or if --asana-task-gid was not specified.
    if asana_task_gid is None:
        if asana_workspace_gid is None:
            if asana_workspace_name is None:
                error_and_exit("Provide either an Asana workspace name or GID to sync.")
        else:
            if asana_workspace_name is not None:
                error_and_exit("Provide either Asana workspace GID or name, but not both.")

        found_workspace = False

        for workspace in asana_client.workspaces.find_all():  # type: ignore
            if workspace["gid"] == asana_workspace_gid:
                asana_workspace_name = workspace["name"]
                found_workspace = True
                break
            if workspace["name"] == asana_workspace_name:
                if found_workspace:
                    error_and_exit(
                        f"Found multiple workspaces with name {asana_workspace_name}. Please"
                        " specify workspace GID instead."
                    )
                else:
                    asana_workspace_gid = workspace["gid"]
                    found_workspace = True
        else:
            if not asana_workspace_gid:
                li = [f"No Asana workspace was found with GID {asana_workspace_gid}"]
                if asana_workspace_name:
                    li.append(f" | Workspace Name: {asana_workspace_name}")
                error_and_exit(f"{' '.join(li)}.")

    # more checks -----------------------------------------------------------------------------
    combination_of_tw_related_options = any([tw_filter_li, tw_tags, tw_project])
    check_required_mutually_exclusive(
        tw_sync_all_tasks,
        combination_of_tw_related_options,
        "sync_all_tw_tasks",
        "combination of specific TW-related options",
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
                "Asana Workspace GID": asana_workspace_gid,
                "Asana Workspace Name": asana_workspace_name,
                "Asana Task GID": asana_task_gid,
            },
            prefix="\n\n",
            suffix="\n",
        )
    )
    if confirm:
        confirm_before_proceeding()

    # initialize sides ------------------------------------------------------------------------
    tw_side = TaskWarriorSide(
        tw_filter=" ".join(tw_filter_li), tags=tw_tags, project=tw_project
    )

    asana_side = AsanaSide(
        client=asana_client, task_gid=asana_task_gid, workspace_gid=asana_workspace_gid
    )

    # teardown function and exception handling ------------------------------------------------
    register_teardown_handler(
        pdb_on_error=pdb_on_error,
        inform_about_config=inform_about_config,
        combination_name=combination_name,
        verbose=verbose,
    )

    # sync ------------------------------------------------------------------------------------
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
