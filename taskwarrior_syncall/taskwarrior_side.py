import datetime
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Set, Union, cast
from uuid import UUID

from bubop import logger, parse_datetime
from taskw import TaskWarrior
from taskw.warrior import TASKRC

from taskwarrior_syncall.sync_side import ItemType, SyncSide
from taskwarrior_syncall.types import TaskwarriorRawItem

OrderByType = Literal[
    "description",
    "end",
    "entry",
    "id",
    "modified",
    "status",
    "urgency",
]


def parse_datetime_(dt: Union[str, datetime.datetime]) -> datetime.datetime:
    if isinstance(dt, datetime.datetime):
        return dt
    else:
        return parse_datetime(dt)


class TaskWarriorSide(SyncSide):
    """Handles interaction with the TaskWarrior client."""

    ID_KEY = "uuid"
    SUMMARY_KEY = "description"
    LAST_MODIFICATION_KEY = "modified"

    def __init__(
        self,
        tags: Sequence[str] = [],
        project: Optional[str] = None,
        config_file: Optional[Path] = Path(TASKRC),
        **kargs,
    ):
        """
        :param tags: List of tags that all fetched and submitted tasks should have
        :param project: project identifier that all fetched and submitted tasks should have
        :param config_file: Path to the taskwarrior RC file
        """
        super().__init__(name="Tw", fullname="Taskwarrior", **kargs)
        self._tags: Set[str] = set(tags)
        self._project: str = project or ""
        self._tw = TaskWarrior(marshal=True, config_filename=config_file)

        # All TW tasks
        self._items_cache: Dict[str, TaskwarriorRawItem] = {}

        # Whether to refresh the cached list of items
        self._reload_items = True

    def start(self):
        logger.info(f"Initializing {self.fullname}...")

    def _load_all_items(self):
        """Load all tasks to memory.

        May return already loaded list of items, depending on the validity of
        the cache.
        """
        if not self._reload_items:
            return

        tasks = self._tw.load_tasks()
        items = [*tasks["completed"], *tasks["pending"]]
        self._items_cache: Dict[str, TaskwarriorRawItem] = {  # type: ignore
            str(item["uuid"]): item for item in items
        }
        self._reload_items = False

    def get_all_items(
        self,
        skip_completed=False,
        order_by: Optional[OrderByType] = None,
        use_ascending_order: bool = True,
        **kargs,
    ) -> List[TaskwarriorRawItem]:
        """
        Fetch the tasks off the local taskw db, taking into account the filters set in the
        during the instance construction.

        :param skip_completed: Skip completed tasks
        :param order_by: specify the order by which to return the items.
        :param use_ascending_order: Boolean flag to specify ascending/descending order
        :return: List of all the tasks
        :raises: ValueError in case the order_by key is invalid
        """
        self._load_all_items()
        tasks = list(self._items_cache.values())
        if skip_completed:
            tasks = [t for t in tasks if t["status"] != "completed"]

        # filter the tasks based on their tags and their project ------------------------------
        if self._tags:
            tasks = [t for t in tasks if self._tags.issubset(t.get("tags", []))]
        if self._project:
            tasks = [t for t in tasks if t.get("project", "") == self._project]

        for task in tasks:
            task["uuid"] = str(task["uuid"])

        if order_by is not None:
            tasks.sort(key=lambda t: t[kargs["order_by"]], reverse=not use_ascending_order)  # type: ignore

        return tasks  # type: ignore

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[TaskwarriorRawItem]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self._tw.get_task(id=item_id)[-1]
            if item is None:
                return None

            # amend cache
            self._items_cache[str(item["uuid"])] = item  # type: ignore
        item["uuid"] = str(item["uuid"])
        return item if item["status"] != "deleted" else None  # type: ignore

    def update_item(self, item_id: str, **changes):
        """Update an already added item.

        :raises ValaueError: In case the item is not present in the db
        """
        changes.pop("id", False)
        t = self._tw.get_task(uuid=UUID(item_id))[-1]

        # task CLI doesn't allow `imask`
        unwanted_keys = ["imask", "recur", "rtype", "parent", "urgency"]
        for i in unwanted_keys:
            t.pop(i, False)

        # taskwarrior doesn't let you explicitly set the update time.
        # even if you set it it will revert to the time  that you call
        # `tw.task_update`
        d = dict(t)
        d.update(changes)
        self._tw.task_update(d)

    def add_item(self, item: ItemType) -> ItemType:
        """Add a new Item as a TW task.

        :param item:  This should contain only keys that exist in standard TW
                      tasks (e.g., proj, tag, due). It is mandatory that it
                      contains the 'description' key for the task title
        """
        item = cast(TaskwarriorRawItem, item)
        assert "description" in item.keys(), "Item doesn't have a description."
        assert (
            "uuid" not in item.keys()
        ), "Item already has a UUID, try updating it instead of adding it"

        curr_status = item.get("status", None)
        if curr_status not in ["pending", "done", "completed"]:
            logger.warning(f'Invalid status of task [{item["status"]}], setting it to pending')  # type: ignore
            item["status"] = "pending"

        if self._tags:
            item["tags"] = list(self._tags.union(item.get("tags", {})))
        if self._project:
            item["project"] = self._project

        description = item.pop("description")
        new_item = self._tw.task_add(description=description, **item)  # type: ignore
        new_id = new_item["id"]
        len_print = min(20, len(description))
        logger.debug(f'Task "{new_id}" created - "{description[0:len_print]}"...')

        return cast(ItemType, new_item)

    def delete_single_item(self, item_id) -> None:
        self._tw.task_delete(uuid=item_id)

    @classmethod
    def id_key(cls) -> str:
        return cls.ID_KEY

    @classmethod
    def summary_key(cls) -> str:
        return cls.SUMMARY_KEY

    @classmethod
    def last_modification_key(cls) -> str:
        return cls.LAST_MODIFICATION_KEY

    @classmethod
    def items_are_identical(
        cls, item1: dict, item2: dict, ignore_keys: Sequence[str] = []
    ) -> bool:
        keys = [
            k
            for k in ["annotations", "description", "due", "status", "uuid"]
            if k not in ignore_keys
        ]

        # special care for the annotations key
        if "annotations" in item1 and "annotations" in item2:
            if item1["annotations"] != item2["annotations"]:
                return False
            item1.pop("annotations")
            item2.pop("annotations")
        # one may contain empty list
        elif "annotations" in item1 and "annotations" not in item2:
            if item1["annotations"] != []:
                return False
            item1.pop("annotations")
        # one may contain empty list
        elif "annotations" in item2 and "annotations" not in item1:
            if item2["annotations"] != []:
                return False
            item2.pop("annotations")
        else:
            pass

        for item in (item1, item2):
            if "uuid" in item:
                item["uuid"] = str(item["uuid"])

            # convert datetime keys to actual datetime objects if they are not.
            if "modified" in item:
                item["modified"] = parse_datetime_(item["modified"])

        return SyncSide._items_are_identical(item1, item2, keys)
