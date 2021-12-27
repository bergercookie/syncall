"""__init__"""


from taskwarrior_syncall.aggregator import Aggregator
from taskwarrior_syncall.app_utils import (
    app_name,
    cache_or_reuse_cached_combination,
    fetch_app_configuration,
    get_config_name_for_args,
    inform_about_combination_name_usage,
    list_named_combinations,
    name_to_resolution_strategy,
    report_toplevel_exception,
)
from taskwarrior_syncall.cli import (
    opt_combination,
    opt_custom_combination_savename,
    opt_gcal_calendar,
    opt_gcal_oauth_port,
    opt_gcal_secret_override,
    opt_list_configs,
    opt_notion_page_id,
    opt_notion_token_pass_path,
    opt_resolution_strategy,
    opt_tw_project,
    opt_tw_tags,
)
from taskwarrior_syncall.sync_side import ItemType, SyncSide
from taskwarrior_syncall.taskwarrior_side import TaskWarriorSide

__all__ = [
    "Aggregator",
    "ItemType",
    "SyncSide",
    "TaskWarriorSide",
    "app_name",
    "cache_or_reuse_cached_combination",
    "fetch_app_configuration",
    "get_config_name_for_args",
    "inform_about_combination_name_usage",
    "list_named_combinations",
    "name_to_resolution_strategy",
    "opt_combination",
    "opt_custom_combination_savename",
    "opt_gcal_calendar",
    "opt_gcal_oauth_port",
    "opt_gcal_secret_override",
    "opt_list_configs",
    "opt_notion_page_id",
    "opt_notion_token_pass_path",
    "opt_resolution_strategy",
    "opt_tw_project",
    "opt_tw_tags",
    "report_toplevel_exception",
]

try:
    from taskwarrior_syncall.notion_side import NotionSide
    from taskwarrior_syncall.tw_notion_utils import convert_notion_to_tw, convert_tw_to_notion

    __all__.extend(["NotionSide", "convert_notion_to_tw", "convert_tw_to_notion"])
except ImportError:
    pass
try:
    from taskwarrior_syncall.gcal_side import GCalSide
    from taskwarrior_syncall.tw_gcal_utils import convert_gcal_to_tw, convert_tw_to_gcal

    __all__.extend(["GCalSide", "convert_gcal_to_tw", "convert_tw_to_gcal"])
except ImportError:
    pass

__version__ = "v1.1.0"
