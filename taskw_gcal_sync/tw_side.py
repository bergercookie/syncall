from taskw_gcal_sync import GenericSide
from taskw import TaskWarrior
import logging
logger = logging.getLogger(__name__)


class TaskWarriorSide(GenericSide):
    """Current class handles the TaskWarrior client."""
    def __init__(self, rem_key="remindme"):
        super(TaskWarriorSide, self).__init__()

        self.side_type = "TW"
        # Reminder tag to be used in the TW side
        self.rem_key = rem_key

        # TaskWarrior instance as a class memeber - initialize only once
        self.tw = TaskWarrior()

    def get_reminders(self):
        """Fetch the reminders off the local taskw db.
        :return: list of reminders that exist locally

        """
        super(TaskWarriorSide, self).get_reminders()
        return self.tw.filter_tasks(filter_dict={'tags': self.rem_key})

    def _add_reminder(self, description, rem):
        """Add a new reminder as a TW task.

        :param summary str Summary of the reminder to be added. Due to the
        taskw Python API this is a separate field
        :param rem dict This should contain only keys that exist in standard TW
        tasks (e.g., proj, tag, due)
        """
        self.tw.task_add(description=description, **rem)




    def update_reminder(self, rem):
        """Apply the list of changed reminders in the local TaskWarrior
        database.

        ..note::
        Reminder doesn't have to contain all the TW task keys but only the ones
        that are to be modified. Reminder to be updated may be a new reminder
        altogether. If so, TaskWarriorSide instance is going to instantiate it
        with a call to the _add_reminder method
        """

        super(TaskWarriorSide, self).update_reminder()

        # TODO - Assert that the reminder has the appropriate reminder tag

        # TODO - Actually apply the changes
        # Reminder may have a valid ID if they already exist in the local
        # db but if they don't, additional reminder tasks are to be added
        raise NotImplementedError("TODO")

    def add_reminder(self, description, **kw):
        super(TaskWarriorSide, self).add_reminder()

        tw = TaskWarrior()
        tw.task_add(description, tag=self.rem_key, **kw)


