from taskw_gcal_sync import GenericSide
from taskw import TaskWarrior
from uuid import UUID
from typing import Any, Dict, Union

class TaskWarriorSide(GenericSide):
    """Handles interaction with the TaskWarrior client."""
    def __init__(self, **kargs):
        super(TaskWarriorSide, self).__init__()

        self.config = {
            'tags': ""
        }
        self.config.update(**kargs)

        # TODO Only single tag versions are currently supported - recheck taskw
        # docs
        if not isinstance(self.config['tags'], str):
            self.logger.fatal(
                "\nPlease provide only a single tag in string form."
                " No other form is currently supported\n")
            raise RuntimeError

        # TaskWarrior instance as a class memeber - initialize only once
        self.tw = TaskWarrior(marshal=True)

    def get_all_items(self, **kargs):
        """Fetch the tasks off the local taskw db.

        :param kargs: Extra options for the call
        :return: list of tasks that exist locally

        """
        include_deleted = kargs.get('include_deleted', False)

        d = {}
        d['tags'] = self.config['tags']

        tasks = self.tw.filter_tasks(filter_dict=d)
        if not include_deleted:
            tasks = [t for t in tasks if t['status'] != 'deleted']
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
        t.update(**changes)
        self.tw.task_update(t)

    def add_item(self, item) -> dict:
        """Add a new Item as a TW task.

        :param item:  This should contain only keys that exist in standard TW
                      tasks (e.g., proj, tag, due). It is mandatory that it
                      contains the 'description' key for the task title
        """
        assert('description' in item)
        len_print = min(10, len(item['desscription']))
        self.logger.info("Adding item - \"{}\"..."
                         .format(item['description'][0:len_print]))
        description = item.pop('description')
        new_item = self.tw.task_add(description=description, **item)

        return new_item
