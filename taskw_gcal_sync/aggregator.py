from taskw_gcal_sync import TaskWarriorSide
from taskw_gcal_sync import GCalSide
from utils import ResolutionNewestWins


class TWGCalAggregator(object):
    """Object is the connector between the TaskWarrior and the Google
    Calendar sides.
    
    Having an aggregator is handy for managing push/pull/sync directives in a
    compact manner.
    
    """
    def __init__(self, resol_strat=ResolutionNewestWins()):
        super(TWGCalAggregator, self).__init__()
        self.tw_side = TaskWarriorSide()
        self.gcal_side = GCalSide()
        self.resol_strat = resol_strat

    def find_diffs(self):
        """Find the differences between the reminders in TW and GCal.

        :return: Dictionary with 3 keys; The first two indicate the **source**
        of the diff and are named ('gcal', 'tw'). The third one indicates the
        conflicts and contains another dictionary with two keys (again 'gcal',
        'tw') holding lists of reminders from the corresponding source
        :rtype: dict

        ..note:
        Current method **does not** take care of the conflict resolution.
        """

        self.tw_side.get_reminders()
        self.gcal_side.get_reminders()

        # Return the dictionary of changes
        raise NotImplementedError("TODO")

    def  resolve_conflicts(conflicts, resolv_strat):
        """TODO.

        :param dict conflicts Dictionary of conflicts. Keys are the same as the
        return type of the find_diffs method
        
        """
        raise NotImplementedError("TODO")
