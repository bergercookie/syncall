"""__init__"""


from taskwarrior_syncall.aggregator import Aggregator
from taskwarrior_syncall.sync_side import SyncSide
from taskwarrior_syncall.taskwarrior_side import TaskWarriorSide
from taskwarrior_syncall.utils import name_to_resolution_strategy

__all__ = [
    "Aggregator",
    "SyncSide",
    "TaskWarriorSide",
    "name_to_resolution_strategy",
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
