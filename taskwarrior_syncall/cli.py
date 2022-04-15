"""CLI argument functions - reuse across your apps."""
import click

from taskwarrior_syncall.app_utils import name_to_resolution_strategy


def opt_list_configs(name_A: str, name_B: str):
    return click.option(
        "--list-configs",
        "do_list_configs",
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
        type=click.Choice(list(name_to_resolution_strategy.keys())),
        help="Resolution strategy to use during conflicts",
    )


def opt_combination(name_A: str, name_B: str):
    return click.option(
        "-b",
        "--combination",
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
        help="Name of the Google Keep Note to synchronize",
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
