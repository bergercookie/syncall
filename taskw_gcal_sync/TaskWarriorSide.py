from typing import Dict, List, Union
from uuid import UUID

from overrides import overrides
from taskw import TaskWarrior

from taskw_gcal_sync.GenericSide import GenericSide
from taskw_gcal_sync.logger import logger


class TaskWarriorSide(GenericSide):
    """Handles interaction with the TaskWarrior client."""

    def __init__(self, **kargs):
        super(TaskWarriorSide, self).__init__()

        # Tags are used to filter the tasks for both *push* and *pull*.
        self.config = {"tags": [], "config_filename": "~/.taskrc", "enable_caching": True}
        self.config.update(**kargs)
        assert isinstance(self.config["tags"], list), "Expected a list of tags"

        # TaskWarrior instance as a class memeber - initialize only once
        self.tw = TaskWarrior(marshal=True, config_filename=self.config["config_filename"])
        # All TW tasks
        self.items: Dict[str, List[dict]] = []
        # Whether to refresh the cached list of items
        self.reload_items = True

    def _load_all_items(self):
        """Load all tasks to memory.

        May return already loaded list of items, depending on the validity of
        the cache.
        """

        if not self.config["enable_caching"]:
            self.items = self.tw.load_tasks()
            return

        if self.reload_items:
            self.items = self.tw.load_tasks()
            self.reload_items = False

    @overrides
    def get_all_items(self, **kargs):
        """Fetch the tasks off the local taskw db.

        :param kargs: Extra options for the call.
            * Use the `order_by` arg to specify the order by which to return the
              items.
            * Use the `use_ascending_order` boolean flag to specify ascending/descending
              order
            * `include_completed` to also include completed tasks [Default: True]
        :return: list of tasks that exist locally
        :raises: ValueError in case the order_by key is invalid

        """
        self._load_all_items()
        tasks = []
        if kargs.get("include_completed", True):
            tasks.extend(self.items["completed"])
        tasks.extend(self.items["pending"])

        tags = set(self.config["tags"])
        tasks = [t for t in tasks if tags.issubset(t.get("tags", []))]

        if "order_by" in kargs and kargs["order_by"] is not None:
            if "use_ascending_order" in kargs:
                assert isinstance(kargs["use_ascending_order"], bool)
                use_ascending_order = kargs["use_ascending_order"]
            else:
                use_ascending_order = True
            assert (
                kargs["order_by"]
                in ["description", "end", "entry", "id", "modified", "status", "urgency"]
                and "Invalid 'order_by' value"
            )
            tasks.sort(key=lambda t: t[kargs["order_by"]], reverse=not use_ascending_order)

        return tasks

    @overrides
    def get_single_item(self, item_id: str) -> Union[dict, None]:
        t = self.tw.get_task(id=item_id)[-1] or None
        assert "status" in t.keys()  # type: ignore
        return t if t["status"] != "deleted" else None  # type: ignore

    @overrides
    def update_item(self, item_id: str, **changes):
        """Update an already added item.

        :raises ValaueError: In case the item is not present in the db
        """
        changes.pop("id", False)
        t = self.tw.get_task(uuid=UUID(item_id))[-1]

        # task CLI doesn't allow `imask`
        unwanted_keys = ["imask", "recur", "rtype", "parent"]
        for i in unwanted_keys:
            t.pop(i, False)

        # taskwarrior doesn't let you explicitly set the update time.
        # even if you set it it will revert to the time  that you call
        # `tw.task_update`
        d = dict(t)
        d.update(changes)
        self.tw.task_update(d)

    @overrides
    def add_item(self, item) -> dict:
        """Add a new Item as a TW task.

        :param item:  This should contain only keys that exist in standard TW
                      tasks (e.g., proj, tag, due). It is mandatory that it
                      contains the 'description' key for the task title
        """
        assert "description" in item.keys(), "Item doesn't have a description."
        assert (
            "uuid" not in item.keys()
        ), "Item already has a UUID, try updating it instead of adding it"

        curr_status = item.get("status", None)
        if curr_status not in ["pending", "done"]:
            logger.info('Invalid status of task: "%s", setting it to pending', item["status"])
            item["status"] = "pending"

        item.setdefault("tags", [])
        item["tags"] += self.config["tags"]

        description = item.pop("description")
        new_item = self.tw.task_add(description=description, **item)
        len_print = min(20, len(description))
        logger.info(
            'Task "{}" created - "{}"...'.format(new_item["id"], description[0:len_print])
        )

        return new_item

    @overrides
    def delete_single_item(self, item_id) -> None:
        self.tw.task_delete(uuid=item_id)

    @staticmethod
    def items_are_identical(item1, item2, ignore_keys=[]) -> bool:

        keys = [
            k
            for k in ["annotations", "description", "due", "modified", "status", "uuid"]
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

        return GenericSide._items_are_identical(item1, item2, keys)

    @staticmethod
    def get_task_id(item: dict) -> str:
        """Get the ID of a task in string form"""
        return str(item["uuid"])
