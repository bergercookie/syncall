from taskw_gcal_sync import GenericSide
from taskw import TaskWarrior
from overrides import overrides
from uuid import UUID
from typing import Dict, List, Union


class TaskWarriorSide(GenericSide):
    """Handles interaction with the TaskWarrior client."""
    def __init__(self, **kargs):
        super(TaskWarriorSide, self).__init__()

        # Tags are used to filter the tasks for both *push* and *pull*.
        self.config = {
            'tags': [],
            'ignore_deleted': True,  # Account for deleted items?
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

    @overrides
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

    @overrides
    def get_single_item(self, item_id: str) -> Union[dict, None]:
        t = self.tw.get_task(id=item_id)[-1] or None
        assert 'status' in t.keys()  # type: ignore
        return t if t['status'] != 'deleted' else None  # type: ignore

    @overrides
    def update_item(self, item_id: str, **changes):
        """Update an already added item.

        :raises ValaueError: In case the item is not present in the db
        """
        changes.pop('id', False)
        t = self.tw.get_task(uuid=UUID(item_id))[-1]

        # task CLI doesn't allow `imask`
        unwanted_keys = ['imask', 'recur', 'rtype', 'parent']
        for i in unwanted_keys:
            t.pop(i, False)

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
        assert 'description' in item.keys(), "Item doesn't have a description."
        assert 'uuid' not in item.keys(), \
            "Item already has a UUID, try updating it instead of adding it"

        curr_status = item.get('status', None)
        if curr_status not in ['pending', 'done']:
            self.logger.info(
                "Invalid status of task: \"%s\", setting it to pending"
                % item['status'])
            item['status'] = 'pending'

        item.setdefault('tags', [])
        item['tags'] += self.config['tags']

        description = item.pop('description')
        new_item = self.tw.task_add(description=description, **item)
        len_print = min(20, len(description))
        self.logger.info("Task \"{}\" created - \"{}\"..."
                         .format(new_item['id'], description[0:len_print]))

        return new_item

    @overrides
    def delete_single_item(self, item_id) -> None:
        self.tw.task_delete(uuid=item_id)
