from typing import Optional, Sequence

import asana

from syncall.asana.asana_task import AsanaTask
from syncall.sync_side import SyncSide
from syncall.types import AsanaGID, AsanaRawTask

# Request up to 100 tasks at a time in GET /tasks API call.
# The API doesn't allow page sizes larger than 100.
GET_TASKS_PAGE_SIZE = 100


class AsanaSide(SyncSide):
    """
    Wrapper class to add/modify/delete asana tasks, etc.
    """

    def __init__(self, client: asana.Client, task_gid: AsanaGID, workspace_gid: AsanaGID):
        self._client = client
        self._task_gid = task_gid
        self._workspace_gid = workspace_gid

        super().__init__(name="Asana", fullname="Asana")

    def start(self):
        pass

    def finish(self):
        pass

    def get_all_items(self, **kwargs) -> Sequence[AsanaTask]:
        results = []

        if self._task_gid is None:
            tasks = self._client.tasks.find_all(
                assignee="me", workspace=self._workspace_gid, page_size=GET_TASKS_PAGE_SIZE
            )

            for task in tasks:
                detailed_task = self.get_item(task["gid"])
                results.append(detailed_task)
        else:
            task = self.get_item(self._task_gid)
            if task is not None:
                results.append(task)

        return results

    def get_item(self, item_id: AsanaGID) -> Optional[AsanaTask]:
        """Get a single item (task) based on the given ID.

        :returns: None if not found, the item (task) in dict representation otherwise
        """
        try:
            return AsanaTask.from_raw_task(self._client.tasks.find_by_id(item_id))
        except asana.error.ForbiddenError:
            # We can get a ForbiddenError when we try to get a task that was
            # permanently deleted on the Asana side.
            return None
        except asana.error.NotFoundError:
            return None

    def delete_single_item(self, item_id: AsanaGID):
        """Delete an item (task) based on the given ID."""
        self._client.tasks.delete_task(item_id)

    def update_item(self, item_id: AsanaGID, **changes):
        """Update with the given item (task).

        :param item_id : ID of item (task) to update
        :param changes: Keyword only parameters that are to change in the item (task)
        .. warning:: The item (task) must already be present
        """
        raw_task = AsanaTask(**changes).to_raw_task()

        # Delete keys that Asana doesn't let us change.
        raw_task.pop("completed_at", None)
        raw_task.pop("created_at", None)
        raw_task.pop("gid", None)
        raw_task.pop("modified_at", None)

        # We need to update either Asana 'due_at' or 'due_on' fields.
        # - If the remote Asana task 'due_on' field is empty, update 'due_at'.
        # - If the remote Asana task 'due_on' field is not empty and the
        #   'due_at' field is empty, update 'due_on'.
        # TODO: find a way to store this information locally, so we don't have
        # to fetch the task from Asana to determine this.
        remote_task = self.get_item(item_id)
        if remote_task.get("due_on", None) is None:
            raw_task.pop("due_on", None)
        elif remote_task.get("due_at", None) is None:
            raw_task.pop("due_at", None)
        else:
            raw_task.pop("due_on", None)

        self._client.tasks.update_task(item_id, raw_task)

    def add_item(self, item: AsanaTask) -> AsanaTask:
        """Add a new item (task).

        :returns: The newly added event
        """
        raw_task = item.to_raw_task()

        if "assignee" not in raw_task:
            raw_task["assignee"] = "me"

        if "workspace" not in raw_task:
            raw_task["workspace"] = self._workspace_gid

        # Delete keys that Asana doesn't let us set.
        raw_task.pop("created_at", None)
        raw_task.pop("modified_at", None)
        raw_task.pop("gid", None)

        # Delete 'due_on' key, rely on 'due_at' instead.
        raw_task.pop("due_on", None)

        return AsanaTask.from_raw_task(self._client.tasks.create_task(raw_task))

    @classmethod
    def id_key(cls) -> str:
        """
        Key in the dictionary of the added/updated/deleted item (task) that refers to the ID of
        that item (task).
        """
        return "gid"

    @classmethod
    def summary_key(cls) -> str:
        """Key in the dictionary of the item (task) that refers to its summary."""
        return "name"

    @classmethod
    def last_modification_key(cls) -> str:
        """Key in the dictionary of the item (task) that refers to its modification date."""
        return "modified_at"

    @classmethod
    def items_are_identical(
        cls, item1: AsanaTask, item2: AsanaTask, ignore_keys: Sequence[str] = []
    ) -> bool:
        """Determine whether two items (tasks) are identical.

        .. returns:: True if items (tasks) are identical, False otherwise.
        """
        compare_keys = AsanaTask._key_names.copy()

        for key in ignore_keys:
            if key in compare_keys:
                compare_keys.remove(key)

        # Special handling for 'due_at' and 'due_on'
        # TODO: reduce ['due_at','due_on'] to 'due_at', compare and remove both
        # keys.
        if item1.get("due_at", None) is not None and item2.get("due_at", None) is not None:
            compare_keys.remove("due_on")
        elif item1.get("due_on", None) is not None and item2.get("due_on", None) is not None:
            compare_keys.remove("due_at")

        return SyncSide._items_are_identical(item1, item2, compare_keys)
