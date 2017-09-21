from taskw_gcal_sync import TaskWarriorSide
from taskw_gcal_sync import GCalSide
from utils import ResolutionNewestWins
from bidict import bidict
import os
import sys
import logging

modules_dir = os.path.join(os.path.dirname(__file__), "..", "third_party")
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
from pypref import SinglePreferences as PREF


class Preferences(PREF):
    # custom_init will still be called in
    # super(Preferences, self).__init__(*args, **kwargs)
    def __init__(self, *args, **kwargs):
        self.ad_lines = []
        self.ad_lines.append(1, "import bidict")


        if self._isInitialized:
            return
        super(Preferences, self).__init__(*args, **kwargs)
        # hereinafter any further instantiation can be coded

    def __dump_file(self, preferences, dynamic, temp=False,
                    ad_lines=self.ad_lines):
        """
        Set preferences and write preferences file by erasing any existing one.
        This is an override of the parent method that also adds aditional lines
        at the given indices.
        
        :Parameters:
            #. preferences (dictionary): The preferences dictionary.
            #. ad_lines (list): list of tuples containing the index and the
            line to be added at that index in the file
            #. dynamic (None, dictionary): The dynamic dictionary. If None dynamic 
               dictionary won't be updated.
        """



logger = logging.getLogger(__name__)


class TWGCalAggregator(object):
    """Object is the connector between the TaskWarrior and the Google
    Calendar sides.
    
    Having an aggregator is handy for managing push/pull/sync directives in a
    compact manner.
    
    """
    def __init__(self, resol_strat=ResolutionNewestWins(), **kargs):
        super(TWGCalAggregator, self, **kargs).__init__()

        self.props = {
            "settings_dir": os.path.join(os.path.expanduser('~'),
                                         ".config",
                                         "taskw_gcal_sync"),
            "settings_fname": "persistent_settings.py"
        }
        self.props.update(**kargs) # Update Properties with the user-set vars

        self.props["settings_fname_full"] = os.path.join(
            self.props["settings_dir"],
            self.props['settings_fname'])

        self.tw_side = TaskWarriorSide()
        self.gcal_side = GCalSide(credentials_dir=self.props["settings_dir"])
        self.resol_strat = resol_strat

        # Correspondences between the TW reminders and the GCal reminder events
        # The following fields are used for finding matches
        # TaskWarrior: uuid
        # GCal: eventId
        self.pref_dict = {"correspndences": bidict(), }

        # Preferences configuration
        # Create preferences directory
        if not os.path.isdir(self.props["settings_dir"]):
            logger.info("Creating preferences path: %s" %
                        self.props["settings_dir"])
            os.makedirs("settings_dir")
        self.pref_file = Preferences(directory=self.props["settings_dir"],
                                     filename=self.props["settings_fname"])

        # Update preferences based on persistent settings
        self.pref_file.update_preferences(self.pref_dict)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def shutdown(self):
        """Method to be called either explicitly or implicitly on instance
        destruction.
        """
        logger.warn("Shutting down instance... %s", __name__)
        self.pref_file.update_preferences(self.pref_dict)


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

        
        tw_rems = self.tw_side.get_reminders()
        gcal_rems = self.gcal_side.get_reminders()

        # Return the dictionary of changes
        raise NotImplementedError("TODO")

    def resolve_conflicts(conflicts, resolv_strat):
        """TODO.

        :param dict conflicts Dictionary of conflicts. Keys are the same as the
        return type of the find_diffs method
        
        """
        raise NotImplementedError("TODO")


    def convert_rem_tw_to_gcal(rem):
        """Convert a TW reminder to a Google Calendar event."""
        raise NotImplementedError("TODO")

    def convert_rem_gcal_to_tw(rem):
        """Convert a GCal event to a TW reminder."""
        raise NotImplementedError("TODO")

    def find_correspondence(self, rem, src='tw'):
        """Based on the format of the given reminder find the one in the other
        format, e.g., given GCal find the corresponding TW reminder

        :param src str Valid options are "tw" and "gcal" (case insensitive).

        Format makes use of the find_correspondence_in_* methods
        """

        return (
            self.find_correspondence_in_tw(self, rem)
            if src.lower() == 'tw'
            else self.find_correspondence_in_gcal(self, rem))


    def find_correspondence_in_tw(self, gcal_rem):
        """Given a GCal reminder event find the corresponding reminder in TW, if the
        latter exists.

        :return: (ID, dict)for corresponding tw reminder, or (None, {}) if a
        valid one is not found
        :rtype: tuple
        """

        assert 'id' in gcal_rem.keys()
        tw_uuid = self.pref_dict.inv[gcal_rem['id']]
        return self.tw_side.tw.get_task(uuid=tw_uuid)

    def find_correspondence_in_gcal(self, tw_rem):
        """Given a TW reminder find the corresponding GCal event, if the
        latter exists.

        :return: ID of corresponding GCal reminder, None if a valid one is not
        found
        """

        assert 'uuid' in tw_rem
        gcal_id = self.pref_dict[tw_rem['uuid']]

        # find GCal reminder based on its id
        self.gcal_side



