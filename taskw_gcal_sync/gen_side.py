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
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def apply_changes(self, changed_rems):
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def reminder_add(self, rem):
        """Add a new reminder."""
        logger.warn("Adding a new reminder task for %s...", self.side_type)
