from typing import Dict, List, Optional
from uuid import UUID

from taskw import TaskWarrior

from taskw_gcal_sync.GenericSide import GenericSide
from taskw_gcal_sync.logger import logger


class TaskWarriorSide(GenericSide):
    """Handles interaction with the TaskWarrior client."""

    def __init__(self, **kargs):
        super(TaskWarriorSide, self).__init__()

        # Tags are used to filter the tasks for both *push* and *pull*.
        self.config = {"tags": [], "config_filename": "~/.taskrc"}
        self.config.update(**kargs)
        assert isinstance(self.config["tags"], list), "Expected a list of tags"

        # TaskWarrior instance as a class memeber - initialize only once
        self.tw = TaskWarrior(marshal=True, config_filename=self.config["config_filename"])
        # All TW tasks
        self.items_cache: Dict[str, dict] = {}
        # Whether to refresh the cached list of items
        self.reload_items = True

    def _load_all_items(self):
        """Load all tasks to memory.

        May return already loaded list of items, depending on the validity of
        the cache.
        """
        if not self.reload_items:
            return

        tasks = self.tw.load_tasks()
        items = [*tasks["completed"], *tasks["pending"]]
        self._items_cache = {item["uuid"]: item for item in items}
        self.reload_items = False

    def get_all_items(
        self,
        skip_completed=False,
        order_by: str = None,
        use_ascending_order: bool = True,
        **kargs,
    ) -> List[dict]:
        """Fetch the tasks off the local taskw db.

        :param skip_completed: Skip completed tasks
        :param order_by: specify the order by which to return the items.
        :param use_ascending_order: Boolean flag to specify ascending/descending order
        :return: List of all the tasks
        :raises: ValueError in case the order_by key is invalid
        """
        self._load_all_items()
        tasks = self._items_cache.values()
        if skip_completed:
            tasks = [t for t in tasks if t["status"] != "completed"]

        tags = set(self.config["tags"])
        tasks = [t for t in tasks if tags.issubset(t.get("tags", []))]
        for task in tasks:
            task["uuid"] = str(task["uuid"])

        if order_by is not None:
            if order_by not in [
                "description",
                "end",
                "entry",
                "id",
                "modified",
                "status",
                "urgency",
            ]:
                raise RuntimeError(f"Invalid order_by value -> {order_by}")
            tasks.sort(key=lambda t: t[kargs["order_by"]], reverse=not use_ascending_order)

        return tasks

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[dict]:
        item = self._items_cache.get(UUID(item_id))
        if not use_cached or item is None:
            item = self.tw.get_task(id=item_id)[-1]
        item["uuid"] = str(item["uuid"])

        return item if item["status"] != "deleted" else None

    def update_item(self, item_id: str, **changes):
        """Update an already added item.

        :raises ValaueError: In case the item is not present in the db
        """
        changes.pop("id", False)
        t = self.tw.get_task(uuid=UUID(item_id))[-1]

        # task CLI doesn't allow `imask`
        unwanted_keys = ["imask", "recur", "rtype", "parent", "urgency"]
        for i in unwanted_keys:
            t.pop(i, False)

        # taskwarrior doesn't let you explicitly set the update time.
        # even if you set it it will revert to the time  that you call
        # `tw.task_update`
        d = dict(t)
        d.update(changes)
        self.tw.task_update(d)

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
        new_id = new_item["id"]
        len_print = min(20, len(description))
        logger.info(f'Task "{new_id}" created - "{description[0:len_print]}"...')

        return new_item

    def delete_single_item(self, item_id) -> None:
        self.tw.task_delete(uuid=item_id)

    @staticmethod
    def items_are_identical(item1, item2, ignore_keys=None) -> bool:
        ignore_keys_ = ignore_keys if ignore_keys is not None else []

        keys = [
            k
            for k in ["annotations", "description", "due", "modified", "status", "uuid"]
            if k not in ignore_keys_
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

        if "uuid" in item1:
            item1["uuid"] = str(item1["uuid"])
        if "uuid" in item2:
            item2["uuid"] = str(item2["uuid"])
        return GenericSide._items_are_identical(item1, item2, keys)

    @staticmethod
    def get_task_id(item: dict) -> str:
        """Get the ID of a task in string form"""
        return str(item["uuid"])
