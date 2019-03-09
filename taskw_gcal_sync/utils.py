import abc


class ResolutionStrategy():
    """Interface for Resolution strategies."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass


    def resolve_conflicts(self, rems):
        """Method for resolving a bunch of reminders.

        :return: Dictionary containing a version of the inputted dictionary
        without the overriden reminders.
        :rtype: dict
        """

        for rem in rems:
            self.resolve_conflict(rem['tw'], rem['gcal'])

    @abc.abstractmethod
    def resolve_conflict(self, item1, item2):
        """Method for resolving a single reminder.

        :return: Index of the chosen reminder; 0 for tw, 1 for gcal
        :rtype: int

        """

        pass


class ResolutionNewestWins(ResolutionStrategy):
    """Conflict resolution strategy which picks the reminder that was last
    modified.
    """

    def __init__(self):
        pass

    def resolve_conflict(self, item1, item2):
        super(ResolutionNewestWins, self).resolve_conflict(item1, item2)
        raise NotImplementedError("TODO")
