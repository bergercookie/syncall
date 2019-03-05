from taskw_gcal_sync import TaskWarriorSide
from taskw_gcal_sync import GCalSide
from taskw_gcal_sync.PrefsManager import PrefsManager
from .utils import ResolutionNewestWins
from bidict import bidict
import atexit
import os
import sys


class TWGCalAggregator():
    """Aggregator class: TaskWarrior <-> Google Calendar sides.

    Having an aggregator is handy for managing push/pull/sync directives in a
    consistent manner.

    """
    def __init__(self, tw_config: dict, gcal_config: dict, **kargs):
        super(TWGCalAggregator, self, **kargs).__init__()

        assert isinstance(tw_config, dict)
        assert isinstance(gcal_config, dict)

        # Preferences manager
        self.prefs_manager = PrefsManager("taskw_gcal_sync")

        # Own config
        self.config = {}
        self.config.update(**kargs)  # Update

        # Sides config + Initialisation
        tw_config_new = {}
        tw_config_new.update(tw_config)
        self.tw_side = TaskWarriorSide(**tw_config_new)

        gcal_config_new = {
            "credentials_dir": self.prefs_manager.prefs_dir_full,
        }
        gcal_config_new.update(tw_config)
        self.gcal_side = GCalSide(**gcal_config_new)

        # Correspondences between the TW reminders and the GCal events
        # The following fields are used for finding matches:
        # TaskWarrior: uuid
        # GCal: eventId
        if "tw_gcal_ids" not in self.prefs_manager:
            self.prefs_manager["tw_gcal_ids"] = bidict()
        self.tw_gcal_ids = self.prefs_manager["tw_gcal_ids"]

        atexit.register(self.cleanup)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def start(self):
        self.tw_side.start()
        self.gcal_side.start()

    def cleanup(self):
        """Method to be called automatically on instance destruction.
        """
        pass


    def find_diffs(self, tw_items, gcal_items):
        """Find the differences between the items in TW and GCal."""
        raise NotImplementedError("TODO")

    def convert_tw_to_gcal(tw_item):
        """Convert a TW item to a Google Calendar event."""
        raise NotImplementedError("TODO")

    def convert_gcal_to_tw(gcal_item):
        """Convert a GCal item to a TW item."""
        raise NotImplementedError("TODO")

    def find_in_tw(self, gcal_item):
        """Given a GCal reminder event find the corresponding reminder in TW, if the
        latter exists.

        :return: (ID, dict)for corresponding tw reminder, or (None, {}) if a
        valid one is not found
        :rtype: tuple
        """

        assert 'id' in gcal_item.keys()
        tw_uuid = self.tw_gcal_ids.inv[gcal_item['id']]
        return self.tw_side.tw.get_task(uuid=tw_uuid)

    def find_in_gcal(self, tw_item):
        """Given a TW reminder find the corresponding GCal event, if the
        latter exists.

        :return: ID of corresponding GCal reminder, None if a valid one is not
        found
        """

        assert 'uuid' in tw_item
        gcal_id = self.tw_gcal_ids[tw_item['uuid']]

        # TODO
