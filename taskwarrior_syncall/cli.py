"""CLI argument functions - reuse across your apps.

This module will be loaded regardless of extras - don't put something here that requires an
extra dependency.
"""
import click

from taskwarrior_syncall.app_utils import name_to_resolution_strategy_type
from taskwarrior_syncall.constants import COMBINATION_FLAGS


def opt_list_combinations(name_A: str, name_B: str):
    return click.option(
        "--list-combinations",
        "do_list_combinations",
        is_flag=True,
        help=f"List the available named {name_A}<->{name_B} combinations",
    )


def opt_tw_tags():
    return click.option(
        "-t",
        "--taskwarrior-tags",
        "tw_tags",
        type=str,
        help="Taskwarrior tags to sync",
        multiple=True,
    )


def opt_tw_project():
    return click.option(
        "-p",
        "--tw-project",
        "tw_project",
        type=str,
        help="Taskwarrior project to sync",
    )


def opt_resolution_strategy():
    return click.option(
        "-r",
        "--resolution_strategy",
        default="AlwaysSecondRS",
        type=click.Choice(list(name_to_resolution_strategy_type.keys())),
        help="Resolution strategy to use during conflicts",
    )


def opt_combination(name_A: str, name_B: str):
    return click.option(
        COMBINATION_FLAGS[0],
        COMBINATION_FLAGS[1],
        "combination_name",
        type=str,
        help=f"Name of an already saved {name_A}<->{name_B} combination",
    )


def opt_custom_combination_savename(name_A: str, name_B: str):
    return click.option(
        "-s",
        "--save-as",
        "custom_combination_savename",
        type=str,
        help=(
            f"Save the given {name_A}<->{name_B} filters combination using a specified custom"
            " name."
        ),
    )


def opt_notion_page_id():
    return click.option(
        "-n",
        "--notion-page",
        "notion_page_id",
        type=str,
        help="Page ID of the Notion page to sync",
    )


def opt_notion_token_pass_path():
    return click.option(
        "--token",
        "--token-pass-path",
        "token_pass_path",
        help="Path in the UNIX password manager to fetch",
        default="notion.so/dev/integration/taskwarrior/token",
    )


def opt_gkeep_user_pass_path():
    return click.option(
        "--user",
        "--user-pass-path",
        "gkeep_user_pass_path",
        help="Path in the UNIX password manager to fetch the Google username from",
        default="gkeepapi/user",
    )


def opt_gkeep_passwd_pass_path():
    return click.option(
        "--passwd",
        "--passwd-pass-path",
        "gkeep_passwd_pass_path",
        help="Path in the UNIX password manager to fetch the Google password from",
        default="gkeepapi/passwd",
    )


def opt_gcal_calendar():
    return click.option(
        "-c",
        "--gcal-calendar",
        type=str,
        help="Name of the Google Calendar to sync (will be created if not there)",
    )


def opt_gkeep_note():
    return click.option(
        "-k",
        "--gkeep-note",
        type=str,
        help=(
            "Full title of the Google Keep Note to synchronize - Make sure you enable the"
            " checkboxes"
        ),
    )


def opt_google_secret_override():
    return click.option(
        "--google-secret",
        default=None,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
        help="Override the client secret used for the communication with the Google APIs",
    )


def opt_google_oauth_port():
    return click.option(
        "--oauth-port",
        default=8081,
        type=int,
        help="Port to use for OAuth Authentication with Google Applications",
    )
