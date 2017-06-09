from taskw_gcal_sync import GenericSide
from taskw import TaskWarrior
import logging
logger = logging.getLogger(__name__)


class TaskWarriorSide(object):
    """Current class handles the taskwarrior client."""
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


    def apply_changes(self, changed_rems):
        """Apply the list of changed reminders in the local TaskWarrior
        database.

        ..note::
        List of changed reminders doesn't have to contain all the TW task keys
        but only the ones that are to be modified

        :param list changed_rems List of reminders that have changed.
        :return: True if changes were successfully applied

        """
        super(TaskWarriorSide, self).apply_changes()

        # TODO - Assert that all reminders have the appropriate reminder tag

        # TODO - Actually apply the changes
        # changed_rems may have a valid ID if they already exist in the local
        # db but if they don't additional reminder tasks are to be added
        raise NotImplementedError("TODO")

    def reminder_add(self, description, **kw):
        super(TaskWarriorSide, self).reminder_add()

        tw = TaskWarrior()
        tw.task_add(description, tag=self.rem_key, **kw)


