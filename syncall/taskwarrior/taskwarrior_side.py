import datetime
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Set,
    Union,
    cast,
)
from uuid import UUID

from bubop import assume_local_tz_if_none, logger, parse_datetime
from taskw import TaskWarrior
from taskw.warrior import TASKRC

from syncall.sync_side import ItemType, SyncSide
from syncall.types import TaskwarriorRawItem

OrderByType = Literal[
    "description",
    "end",
    "entry",
    "id",
    "modified",
    "status",
    "urgency",
]

tw_duration_key = "twgcalsyncduration"
tw_config_default_overrides = {"context": "none", f"uda.{tw_duration_key}.type": "duration"}


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
        tags: Sequence[str] = tuple(),
        project: Optional[str] = None,
        only_modified_since: Optional[datetime.datetime] = None,
        config_file: Path = Path(TASKRC),
        config_overrides: Mapping[str, Any] = {},
        **kargs,
    ):
        """
        Constructor.

        :param tags: Only include tasks that have are tagged using *all* the specified tags
        :param project: Only include tasks that include in this project
        :param only_modified_since: Only include tasks that are modified since the specified date
        :param config_file: Path to the taskwarrior RC file
        :param config_overrides: Dictionary of taskrc key, values to override. See also
                                 tw_config_default_overrides
        """
        super().__init__(name="Tw", fullname="Taskwarrior", **kargs)
        self._tags: Set[str] = set(tags)
        self._project: str = project or ""

        config_overrides_ = tw_config_default_overrides.copy()
        config_overrides_.update(config_overrides)

        self._tw = TaskWarrior(
            marshal=True, config_filename=str(config_file), config_overrides=config_overrides_
        )

        # All TW tasks
        self._items_cache: Dict[str, TaskwarriorRawItem] = {}

        # Whether to refresh the cached list of items
        self._reload_items = True

        self._only_modified_since = only_modified_since

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
            tasks = [t for t in tasks if t["status"] != "completed"]  # type: ignore

        # filter the tasks based on their tags, project and modification date -----------------
        def create_tasks_filter() -> Callable[[TaskwarriorRawItem], bool]:
            always_true = lambda task: True
            fn = always_true

            tags_fn = lambda task: self._tags.issubset(task.get("tags", []))
            project_fn = lambda task: task.get("project", "") == self._project

            if self._only_modified_since:
                mod_since_date = assume_local_tz_if_none(self._only_modified_since)

                def only_modified_since_fn(task):
                    mod_date = task.get("modified")
                    if mod_date is None:
                        logger.warning(
                            f'Task does not have a modification date {task["uuid"]}, this'
                            " sounds like a bug but including it anyway..."
                        )
                        return True

                    mod_date: datetime.datetime
                    mod_date = assume_local_tz_if_none(mod_date)

                    if mod_since_date <= mod_date:
                        return True

                    return False

            if self._tags:
                fn = lambda task, fn=fn, tags_fn=tags_fn: fn(task) and tags_fn(task)
            if self._project:
                fn = lambda task, fn=fn, project_fn=project_fn: fn(task) and project_fn(task)
            if self._only_modified_since:
                fn = lambda task, fn=fn: fn(task) and only_modified_since_fn(task)

            return fn

        tasks_filter = create_tasks_filter()
        tasks = [t for t in tasks if tasks_filter(t)]

        for task in tasks:
            task["uuid"] = str(task["uuid"])  # type: ignore

        if order_by is not None:
            tasks.sort(key=lambda t: t[kargs["order_by"]], reverse=not use_ascending_order)  # type: ignore

        return tasks

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
        len_print = min(20, len(description))
        logger.trace(f'Adding task "{description[0:len_print]}" with properties:\n\n{item}')
        new_item = self._tw.task_add(description=description, **item)  # type: ignore
        new_id = new_item["id"]
        logger.debug(f'Task "{new_id}" created - "{description[0:len_print]}"...')

        # explicitly mark as deleted - taskw doesn't like task_add(`status:deleted`) so we have
        # todo it in two steps
        if curr_status == "deleted":
            logger.debug(
                f'Task "{new_id}" marking as deleted - "{description[0:len_print]}"...'
            )
            self._tw.task_delete(id=new_id)

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
            for k in [
                "annotations",
                "description",
                "scheduled",
                "due",
                "status",
                "uuid",
                tw_duration_key,
            ]
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
