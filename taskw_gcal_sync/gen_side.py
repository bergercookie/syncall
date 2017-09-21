import abc
import logging
logger = logging.getLogger(__name__)


class GenericSide(object):
    """Common parent for classes implementing specfic sides (i.e. GCal, TW)."""

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(GenericSide, self).__init__()
        self.side_type = None



    @abc.abstractmethod
    def get_reminders(self):
        """Return a list of reminders.

        :return: A list of items is returned. The type of these items depends
        on the derived class
        :rtype: list
        """
        raise NotImplementedError("Should be implemented in derived")


    def update_reminders(self, rems):
        """Update the db with the list of reminders.

        This constitudes a wrapper around the update_reminder method.

        :param rems list List of reminders with which to update the side of the
        derived class.
        :return: True if changes were successfully applied
        """
        for rem in rems:
            self.update_reminder(rem)

    @abc.abstractmethod
    def update_reminder(self, rem):
        """Update with the given reminder. This is a common call for both
        updatign an already initialized reminder as well as initializing a new
        one
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def _add_reminder(self, rem):
        """Private method, called by update_reminder for initializing a new
        reminder."""


