"""CLI argument functions - reuse across your apps.

This module will be loaded regardless of extras - don't put something here that requires an
extra dependency.
"""

import os
import sys

import click
from bubop import format_list, logger

from syncall import __version__
from syncall.app_utils import (
    determine_app_config_fname,
    error_and_exit,
    fetch_from_pass_manager,
    get_named_combinations,
    name_to_resolution_strategy_type,
)
from syncall.constants import COMBINATION_FLAGS
from syncall.pdb_cli_utils import run_pdb_on_error as _run_pdb_on_error


def _set_own_excepthook(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return value

    sys.excepthook = _run_pdb_on_error
    return value


def _opt_pdb_on_error():
    return click.option(
        "--pdb-on-error",
        "pdb_on_error",
        is_flag=True,
        help="Invoke PDB if there's an uncaught exception during the program execution.",
        callback=_set_own_excepthook,
        expose_value=True,
        is_eager=True,
    )


# asana related options -----------------------------------------------------------------------
def opts_asana(hidden_gid: bool):
    def decorator(f):
        for d in reversed(
            [
                _opt_asana_token_pass_path,
                _opt_asana_workspace_gid,
                _opt_asana_workspace_name,
                _opt_list_asana_workspaces,
            ]
        ):
            f = d()(f)

        # --asana-task-gid is used to ease development and debugging. It is not currently
        # suitable for regular use.
        f = _opt_asana_task_gid(hidden=hidden_gid)(f)

        return f

    return decorator


def _opt_asana_task_gid(**kwargs):
    return click.option(
        "-a",
        "--asana-task-gid",
        "asana_task_gid",
        type=str,
        help="Limit sync to provided task",
        **kwargs,
    )


def _opt_asana_token_pass_path():
    def callback(ctx, param, value):
        api_token_pass_path = value

        # fetch API token to connect to asana -------------------------------------------------
        asana_token = os.environ.get("ASANA_PERSONAL_ACCESS_TOKEN")

        if asana_token is None and api_token_pass_path is None:
            error_and_exit(
                "You must provide an Asana Personal Access asana_token, using the"
                f" {'/'.join(param.opts)} option"
            )
        if asana_token is not None:
            logger.debug(
                "Reading the Asana Personal Access asana_token (PAT) from environment"
                " variable..."
            )
        else:
            asana_token = fetch_from_pass_manager(api_token_pass_path)

        return asana_token

    return click.option(
        "--token",
        "--token-pass-path",
        "asana_token",
        help="Path in the UNIX password manager to fetch",
        expose_value=True,
        callback=callback,
    )


def _opt_asana_workspace_gid():
    return click.option(
        "-w",
        "--asana-workspace-gid",
        "asana_workspace_gid",
        type=str,
        help="Asana workspace GID used to filter tasks",
    )


def _opt_asana_workspace_name():
    return click.option(
        "-W",
        "--asana-workspace-name",
        "asana_workspace_name",
        type=str,
        help="Asana workspace name used to filter tasks",
    )


def _opt_list_asana_workspaces():
    return click.option(
        "--list-asana-workspaces",
        "do_list_asana_workspaces",
        is_flag=True,
        help="List the available Asana workspaces",
    )


# taskwarrior options -------------------------------------------------------------------------
def opts_tw_filtering():
    def decorator(f):
        for d in reversed(
            [
                _opt_tw_filter,
                _opt_tw_all_tasks,
                _opt_tw_tags,
                _opt_tw_project,
                _opt_tw_only_tasks_modified_X_days,
                _opt_prefer_scheduled_date,
            ]
        ):
            f = d()(f)
        return f

    return decorator


def _opt_tw_filter():
    return click.option(
        "-f",
        "--tw-filter",
        "tw_filter",
        type=str,
        help=(
            "Taskwarrior filter for specifying the tasks to synchronize. These filters will be"
            " concatenated using AND with potential tags and projects potentially specified."
        ),
    )


def _opt_tw_all_tasks():
    return click.option(
        "--all",
        "--taskwarrior-all-tasks",
        "tw_sync_all_tasks",
        is_flag=True,
        help="Sync all taskwarrior tasks (potentially very slow).",
    )


def _opt_tw_tags():
    return click.option(
        "-t",
        "--taskwarrior-tags",
        "tw_tags",
        type=str,
        help="Taskwarrior tags to synchronize.",
        expose_value=True,
        multiple=True,
    )


def _opt_tw_project():
    return click.option(
        "-p",
        "--tw-project",
        "tw_project",
        type=str,
        help="Taskwarrior project to synchronize.",
        expose_value=True,
        is_eager=True,
    )


def _opt_tw_only_tasks_modified_X_days():
    def callback(ctx, param, value):
        if value is None or ctx.resilient_parsing:
            return

        return f"modified.after:-{value}d"

    return click.option(
        "--days",
        "--only-modified-last-X-days",
        "tw_only_modified_last_X_days",
        type=str,
        help=(
            "Only synchronize Taskwarrior tasks that have been modified in the last X days"
            " (specify X, e.g., 1, 30, 0.5, etc.)."
        ),
        callback=callback,
    )


def _opt_prefer_scheduled_date():
    return click.option(
        "--prefer-scheduled-date",
        "prefer_scheduled_date",
        is_flag=True,
        help=(
            'Prefer using the "scheduled" date field instead of the "due" date if the former'
            " is available."
        ),
    )


# notion --------------------------------------------------------------------------------------
def opt_notion_page_id():
    return click.option(
        "-n",
        "--notion-page",
        "notion_page_id",
        type=str,
        help="Page ID of the Notion page to synchronize.",
    )


def opt_notion_token_pass_path():
    return click.option(
        "--token",
        "--token-pass-path",
        "token_pass_path",
        help="Path in the UNIX password manager to fetch.",
    )


# gkeep ---------------------------------------------------------------------------------------
def opts_gkeep():
    def decorator(f):
        for d in reversed(
            [
                _opt_gkeep_user_pass_path,
                _opt_gkeep_passwd_pass_path,
                _opt_gkeep_token_pass_path,
            ]
        ):
            f = d()(f)

        return f

    return decorator


def _opt_gkeep_user_pass_path():
    return click.option(
        "--user",
        "--user-pass-path",
        "gkeep_user_pass_path",
        help="Path in the UNIX password manager to fetch the Google username from.",
        default="gkeepapi/user",
    )


def _opt_gkeep_passwd_pass_path():
    return click.option(
        "--passwd",
        "--passwd-pass-path",
        "gkeep_passwd_pass_path",
        help="Path in the UNIX password manager to fetch the Google password from.",
        default="gkeepapi/passwd",
    )


def _opt_gkeep_token_pass_path():
    return click.option(
        "--token",
        "--token-pass-path",
        "gkeep_token_pass_path",
        help="Path in the UNIX password manager to fetch the google keep token from.",
        default="gkeepapi/token",
    )


def opt_gkeep_labels():
    return click.option(
        "-k",
        "--gkeep-labels",
        type=str,
        multiple=True,
        help="Google Keep labels whose notes to synchronize.",
    )


def opt_gkeep_ignore_labels():
    return click.option(
        "-i",
        "--gkeep-ignore-labels",
        type=str,
        multiple=True,
        help="Google Keep labels whose notes will be explicitly ignored.",
    )


def opt_gkeep_note():
    return click.option(
        "-k",
        "--gkeep-note",
        type=str,
        help=(
            "Full title of the Google Keep Note to synchronize - Make sure you enable the"
            " checkboxes."
        ),
    )


# google calendar -----------------------------------------------------------------------------
def opt_gcal_calendar():
    return click.option(
        "-c",
        "--gcal-calendar",
        type=str,
        help="Name of the Google Calendar to synchronize (will be created if not there).",
    )


# google tasks --------------------------------------------------------------------------------
def opt_gtasks_list():
    return click.option(
        "-l",
        "--gtasks-list",
        type=str,
        help="Name of the Google Tasks list to synchronize (will be created if not there).",
    )


# google-related options ----------------------------------------------------------------------
def opt_google_secret_override():
    return click.option(
        "--google-secret",
        default=None,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
        help="Override the client secret used for the communication with the Google APIs.",
    )


def opt_google_oauth_port():
    return click.option(
        "--oauth-port",
        default=8081,
        type=int,
        help="Port to use for OAuth Authentication with Google Applications.",
    )


# caldav options ------------------------------------------------------------------------------
def opts_caldav():
    def decorator(f):
        for d in reversed(
            [
                _opt_caldav_calendar,
                _opt_caldav_url,
                _opt_caldav_user,
                _opt_caldav_passwd_pass_path,
                _opt_caldav_passwd_cmd,
            ]
        ):
            f = d()(f)

        return f

    return decorator


def _opt_caldav_calendar():
    return click.option(
        "--caldav-calendar",
        type=str,
        default="Personal",
        help="Name of the caldav Calendar to sync (will be created if not there).",
    )


def _opt_caldav_url():
    return click.option(
        "--caldav-url",
        type=str,
        help="URL where the caldav calendar is hosted at (including /dav if applicable).",
    )


def _opt_caldav_user():
    return click.option(
        "--caldav-user",
        "caldav_user",
        help="The caldav username for the given caldav instance",
    )


def _opt_caldav_passwd_pass_path():
    return click.option(
        "--caldav-passwd",
        "--caldav-passwd-pass-path",
        "caldav_passwd_pass_path",
        help="Path in the UNIX password manager to fetch the caldav password from.",
    )


def _opt_caldav_passwd_cmd():
    return click.option(
        "--caldav-passwd-cmd",
        "caldav_passwd_cmd",
        help="Command that outputs the caldav password on stdout.",
    )


# filesystem related options ------------------------------------------------------------------
def opt_filesystem_root():
    return click.option(
        "--fs",
        "--fs-root",
        "filesystem_root",
        required=False,
        type=str,
        help="Directory to consider as root for synchronization operations.",
    )


def opt_filename_extension():
    return click.option(
        "--ext",
        "--filename-extension",
        "filename_extension",
        type=str,
        help="Use this extension for locally created files.",
        default=".md",
    )


# general options -----------------------------------------------------------------------------
def opts_miscellaneous(side_A_name: str, side_B_name: str):
    def decorator(f):
        for d in reversed(
            [
                (_opt_list_resolution_strategies,),
                (_opt_resolution_strategy,),
                (_opt_confirm,),
                (
                    click.version_option,
                    __version__,
                ),
                (_opt_pdb_on_error,),
                (_opt_list_combinations, side_A_name, side_B_name),
                (_opt_combination, side_A_name, side_B_name),
                (_opt_custom_combination_savename, side_A_name, side_B_name),
            ]
        ):
            fn = d[0]
            fn_args = d[1:]
            f = fn(*fn_args)(f)  # type: ignore

        f = click.option("-v", "--verbose", count=True)(f)
        return f

    return decorator


def _opt_confirm():
    return click.option(
        "--confirm",
        "confirm",
        is_flag=True,
        default=False,
        expose_value=True,
        help="Confirm app configuration before proceeding with the actual execution",
    )


def opt_default_duration_event_mins():
    return click.option(
        "--default-event-duration-mins",
        "default_event_duration_mins",
        default=30,
        type=int,
        help="The default duration of an event that is to be created [in minutes].",
    )


def _list_named_combinations(config_fname: str) -> None:
    """List the named configurations currently available for the given configuration name."""
    logger.success(
        format_list(
            header="\n\nNamed configurations currently available",
            items=get_named_combinations(config_fname=config_fname),
        )
    )


def _opt_list_combinations(side_A_name: str, side_B_name: str):
    def callback(ctx, param, value):
        if value is True:
            _list_named_combinations(
                config_fname=determine_app_config_fname(
                    side_A_name=side_A_name, side_B_name=side_B_name
                )
            )
            sys.exit(0)

    return click.option(
        "--list-combinations",
        "do_list_combinations",
        is_flag=True,
        expose_value=False,
        help=f"List the available named {side_A_name}<->{side_B_name} combinations.",
        callback=callback,
    )


def _opt_resolution_strategy():
    return click.option(
        "-r",
        "--resolution-strategy",
        default="AlwaysSecondRS",
        type=click.Choice(list(name_to_resolution_strategy_type.keys())),
        help="Resolution strategy to use during conflicts.",
    )


def _opt_list_resolution_strategies():
    def _list_resolution_strategies(ctx, param, value):
        if value is not True:
            return

        strs = name_to_resolution_strategy_type.keys()
        click.echo("\n".join([f"{a}. {b}" for a, b in zip(range(1, len(strs) + 1), strs)]))
        sys.exit(0)

    return click.option(
        "--list-resolution-strategies",
        callback=_list_resolution_strategies,
        is_flag=True,
        expose_value=False,
        help="List all the available resolution strategies and exit.",
    )


def _opt_combination(side_A_name: str, side_B_name: str):
    return click.option(
        COMBINATION_FLAGS[0],
        COMBINATION_FLAGS[1],
        "combination_name",
        type=str,
        help=f"Name of an already saved {side_A_name}<->{side_B_name} combination.",
    )


def _opt_custom_combination_savename(side_A_name: str, side_B_name: str):
    return click.option(
        "-s",
        "--save-as",
        "custom_combination_savename",
        type=str,
        help=(
            f"Save the given {side_A_name}<->{side_B_name} filters combination using a"
            " specified custom name."
        ),
    )
