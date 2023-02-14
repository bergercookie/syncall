"""__init__"""

# global imports ------------------------------------------------------------------------------
from syncall.aggregator import Aggregator
from syncall.app_utils import (
    app_name,
    cache_or_reuse_cached_combination,
    fetch_app_configuration,
    fetch_from_pass_manager,
    get_config_name_for_args,
    get_resolution_strategy,
    inform_about_app_extras,
    inform_about_combination_name_usage,
    list_named_combinations,
    name_to_resolution_strategy_type,
    report_toplevel_exception,
)
from syncall.cli import (
    opt_asana_task_gid,
    opt_asana_token_pass_path,
    opt_asana_workspace_gid,
    opt_asana_workspace_name,
    opt_combination,
    opt_custom_combination_savename,
    opt_filesystem_root,
    opt_gcal_calendar,
    opt_gkeep_labels,
    opt_gkeep_note,
    opt_gkeep_passwd_pass_path,
    opt_gkeep_user_pass_path,
    opt_google_oauth_port,
    opt_google_secret_override,
    opt_list_asana_workspaces,
    opt_list_combinations,
    opt_notion_page_id,
    opt_notion_token_pass_path,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
)
from syncall.sync_side import ItemType, SyncSide

__all__ = [
    "Aggregator",
    "ItemType",
    "SyncSide",
    "app_name",
    "cache_or_reuse_cached_combination",
    "fetch_app_configuration",
    "fetch_from_pass_manager",
    "get_config_name_for_args",
    "inform_about_app_extras",
    "inform_about_combination_name_usage",
    "list_named_combinations",
    "get_resolution_strategy",
    "name_to_resolution_strategy_type",
    "opt_asana_task_gid",
    "opt_asana_token_pass_path",
    "opt_asana_workspace_gid",
    "opt_asana_workspace_name",
    "opt_combination",
    "opt_custom_combination_savename",
    "opt_gcal_calendar",
    "opt_gkeep_note",
    "opt_gkeep_passwd_pass_path",
    "opt_gkeep_user_pass_path",
    "opt_google_oauth_port",
    "opt_google_secret_override",
    "opt_list_asana_workspaces",
    "opt_list_combinations",
    "opt_notion_page_id",
    "opt_notion_token_pass_path",
    "opt_resolution_strategy",
    "opt_tw_project",
    "opt_filesystem_root",
    "opt_tw_tags",
    "opt_gkeep_labels",
    "report_toplevel_exception",
]

# asana ----------------------------------------------------------------------------------------
try:
    from syncall.asana.asana_side import AsanaSide
    from syncall.asana.utils import list_asana_workspaces
    from syncall.tw_asana_utils import convert_asana_to_tw, convert_tw_to_asana

    __all__.extend(
        ["AsanaSide", "convert_asana_to_tw", "convert_tw_to_asana", "list_asana_workspaces"]
    )
except ImportError:
    pass

# tw ------------------------------------------------------------------------------------------
try:
    from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide

    __all__.extend(
        [
            "TaskWarriorSide",
        ]
    )
except ImportError:
    pass

# notion --------------------------------------------------------------------------------------
try:
    from syncall.notion.notion_side import NotionSide

    __all__.extend(["NotionSide"])
except ImportError:
    pass

# notion <> tw --------------------------------------------------------------------------------
try:
    from syncall.tw_notion_utils import convert_notion_to_tw, convert_tw_to_notion

    __all__.extend(["convert_notion_to_tw", "convert_tw_to_notion"])
except ImportError:
    pass

# gcal ----------------------------------------------------------------------------------------
try:
    from syncall.google.gcal_side import GCalSide
    from syncall.tw_gcal_utils import convert_gcal_to_tw, convert_tw_to_gcal
except ImportError:
    __all__.extend(
        [
            "GCalSide",
            "convert_gcal_to_tw",
            "convert_tw_to_gcal",
        ]
    )

# gkeep ---------------------------------------------------------------------------------------
try:
    from syncall.google.gkeep_note import GKeepNote
    from syncall.google.gkeep_note_side import GKeepNoteSide
    from syncall.google.gkeep_todo_item import GKeepTodoItem
    from syncall.google.gkeep_todo_side import GKeepTodoSide

    __all__.extend(
        [
            "GKeepNote",
            "GKeepNoteSide",
            "GKeepTodoItem",
            "GKeepTodoSide",
            "convert_gkeep_todo_to_tw",
            "convert_tw_to_gkeep_todo",
        ]
    )
except ImportError:
    pass

# gkeep <> tw
try:
    from syncall.tw_gkeep_utils import convert_gkeep_todo_to_tw, convert_tw_to_gkeep_todo

    __all__.extend(
        [
            "convert_gkeep_todo_to_tw",
            "convert_tw_to_gkeep_todo",
        ]
    )
except ImportError:
    pass

# filesytem -----------------------------------------------------------------------------------
try:
    from syncall.filesystem.filesystem_file import FilesystemFile
    from syncall.filesystem.filesystem_side import FilesystemSide

    __all__.extend(["FilesystemFile", "FilesystemSide"])
except ImportError:
    pass


# filesytem <> gkeep --------------------------------------------------------------------------
try:
    from syncall.filesystem_gkeep_utils import (
        convert_filesystem_file_to_gkeep_note,
        convert_gkeep_note_to_filesystem_file,
    )

    __all__.extend(
        ["convert_filesystem_file_to_gkeep_note", "convert_gkeep_note_to_filesystem_file"]
    )
except ImportError:
    pass

__version__ = "1.5.1"
