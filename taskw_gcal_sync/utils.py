import abc
import logging
logger = logging.getLogger(__name__)


class ResolutionStrategy(object):
    """Abstract class that defines an interface for derived strategies."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(ResolutionStrategy, self).__init__()
        logger.info("Initializing resolution strategy...")
        self.strat_str = None


    def resolve_conflicts(self, rems):
        """Method for resolving a bunch of reminders.
        
        :return: Dictionary containing a version of the inputted dictionary
        without the overriden reminders.
        :rtype: dict
        """

        logger.info("Resolving conflicts, strategy: %s", self.strat_str)
        for rem in rems:
            self.resolve_conflict(rem['tw'], rem['gcal'])

    @abc.abstractmethod
    def resolve_conflict(self, tw_rem, gcal_rem):
        """Method for resolving a single reminder.

        :return: Index of the chosen reminder; 0 for tw, 1 for gcal
        :rtype: int

        """
        logger.info("Resolving individual conflict...")
        

class ResolutionNewestWins(ResolutionStrategy):
    """Conflict resolution strategy which picks the reminder that was last
    modified.
    """

    def __init__(self):
        super(ResolutionNewestWins, self).__init__()
        self.strat_str = "newest"

    def resolve_conflict(self, tw_rem, gcal_rem):
        super(ResolutionNewestWins, self).resolve_conflict()
        raise NotImplementedError("TODO")
 
