from taskw_gcal_sync import GenericSide
from taskw import TaskWarrior
from uuid import UUID
from typing import Any, Dict, List, Union

class TaskWarriorSide(GenericSide):
    """Handles interaction with the TaskWarrior client."""
    def __init__(self, **kargs):
        super(TaskWarriorSide, self).__init__()

        # Tags are used to filter the tasks for both *push* and *pull*.
        self.config = {
            'tags': []
        }
        self.config.update(**kargs)
        assert isinstance(self.config['tags'], list), \
            'Expected a list of tags'

        # TaskWarrior instance as a class memeber - initialize only once
        self.tw = TaskWarrior(marshal=True)
        # All TW tasks
        self.items: Dict[str, List[dict]] = []
        # Whether to refresh the cached list of items
        self.reload_items = True

    def _load_all_items(self):
        """Load all tasks to memory.

        May return already loaded list of items, depending on the validity of
        the cache.
        """

        if self.reload_items:
            self.items = self.tw.load_tasks()
            self.reload_items = False

    def get_all_items(self, **kargs):
        """Fetch the tasks off the local taskw db.

        :param kargs: Extra options for the call
        :return: list of tasks that exist locally

        """
        self._load_all_items()
        tasks = self.items['completed'] + self.items['pending']

        tags = set(self.config['tags'])
        tasks = [t for t in tasks if tags.issubset(t.get('tags', []))]
        return tasks

    def get_single_item(self, _id: str) -> Union[dict, None]:
        t = self.tw.get_task(id=_id)[-1] or None
        return t

    def update_item(self, item_id: str, **changes):
        """Update an already added item.

        :raises ValaueError: In case the item is not present in the db
        """
        if 'id' in changes.keys():
            changes.pop(id)  # type: ignore
        t = self.tw.get_task(uuid=UUID(item_id))[-1]
        d = dict(t)
        d.update(changes)
        self.tw.task_update(d)

    def add_item(self, item) -> dict:
        """Add a new Item as a TW task.

        :param item:  This should contain only keys that exist in standard TW
                      tasks (e.g., proj, tag, due). It is mandatory that it
                      contains the 'description' key for the task title
        """
        assert 'description' in item.keys(), "Item doesn't have a description."
        assert 'uuid' not in item.keys(), \
            "Item already has a UUID, try updating it instead of adding it"

        curr_status = item.get('status', None)
        if curr_status not in ['pending', 'done']:
            self.logger.info("Invalid status of task: {}, setting it to pending"
                             .format(item['status']))
            item['status'] = 'pending'

        item.setdefault('tags', [])
        item['tags'] += self.config['tags']

        description = item.pop('description')
        new_item = self.tw.task_add(description=description, **item)
        len_print = min(10, len(description))
        self.logger.info("Task \"{}\" created - \"{}\"..."
                         .format(new_item['id'], description[0:len_print]))

        return new_item
