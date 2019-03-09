from taskw_gcal_sync import GCalSide
from taskw_gcal_sync import TaskWarriorSide
from taskw_gcal_sync.PrefsManager import PrefsManager
from taskw_gcal_sync.clogger import setup_logging

from bidict import bidict
from typing import Any, Tuple, List, Dict, Union
import atexit
import logging
import os
import sys

from uuid import UUID
from datetime import datetime, timedelta
from dateutil.tz import tzutc

logger = logging.getLogger(__name__)
setup_logging(__name__)

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

    def compare_tw_gcal_items(self, tw_item, gcal_item) -> Any:
        """Compare a TW and a GCal item and find any differences.

        :returns: True if there is no difference, tuple of tuples of keys of
                  that they differ at otherwise
        """
        # 'update' time shouldn't matter on whether two items are identical
        raise NotImplementedError("TODO")

    def is_same_event(self, tw_item, gcal_item) -> bool:
        """
        Returns True if the events are equivalent (check ID/UUID
        correspondence), False otherwise
        """

        # Check the bidict
        raise NotImplementedError("TODO")

    @staticmethod
    def convert_tw_to_gcal(tw_item: dict) -> dict:
        """Convert a TW item to a Gcal event.

        .. note:: Do not convert the ID as that may change either manually or
                  after marking the task as "DONE"
        """

        assert all([i in tw_item.keys()
                    for i in ['description', 'status', 'uuid']]) and \
            "Missing keys in tw_item"

        gcal_item = {}

        # Summary
        gcal_item['summary'] = tw_item['description']

        # description
        gcal_item['description'] = "{meta_title}\n"\
            .format(desc=tw_item['description'],
                    meta_title='IMPORTED FROM TASKWARRIOR',)
        if 'annotations' in tw_item.keys():
            for i, a in enumerate(tw_item['annotations']):
                gcal_item['description'] += '\n* Annotation {}: {}' \
                    .format(i+1, a)

        gcal_item['description'] += '\n'
        for k in ['status', 'uuid']:
            gcal_item['description'] += '\n* {}: {}'.format(k, tw_item[k])

        # Handle dates:
        # - If given due date -> (start=entry, end=due)
        # - Else -> (start=entry, end=entry+1)
        entry_dt = GCalSide.format_datetime(tw_item['entry'])
        gcal_item['start'] = \
            {'dateTime': entry_dt}
        if 'due' in tw_item.keys():
            due_dt = GCalSide.format_datetime(tw_item['due'])
            gcal_item['end'] = {'dateTime': due_dt}
        else:
            gcal_item['end'] = {'dateTime': GCalSide.format_datetime(
                tw_item['entry'] + timedelta(days=1))}

        return gcal_item

    @staticmethod
    def convert_gcal_to_tw(gcal_item: dict) -> dict:
        """Convert a GCal event to a TW item."""
        annotations, status, uuid = \
            TWGCalAggregator._parse_gcal_item_desc(gcal_item)
        assert isinstance(annotations, list)
        assert isinstance(status, str)
        assert isinstance(uuid, UUID) or uuid is None

        tw_item: Dict[str, Any] = {}
        # annotations
        tw_item['annotations'] = annotations
        # Status
        if status not in ['pending', 'completed', 'deleted', 'waiting',
                          'recurring']:
            logger.warn(
                "Invalid status %s in GCal->TW conversion of item:" % status)
        else:
            tw_item['status'] = status

        # uuid - may just be created -, thus not there
        if uuid is not None:
            tw_item['uuid'] = uuid

        # Description
        tw_item['description'] = gcal_item['summary']

        # entry
        tw_item['entry'] = GCalSide.parse_datetime(gcal_item['start']['dateTime'])
        tw_item['due'] = GCalSide.parse_datetime(gcal_item['end']['dateTime'])

        # Note:
        # Don't add extra fields of GCal as TW annotations 'cause then, if
        # converted backwards, these annotations are going in the description of
        # the Gcal event and then these are going into the event description and
        # this happens on every conversion. Add them as new TW UDAs if needed

        # add annotation
        return tw_item

    @staticmethod
    def _parse_gcal_item_desc(gcal_item: dict) -> Tuple[List[str], str,
                                                        Union[UUID, None]]:
        """Parse the necessary TW fields off a Google Calendar Item.

        """
        annotations: List[str] = []
        status = 'pending'
        uuid = None

        if 'description' not in gcal_item.keys():
            return annotations, status, uuid

        gcal_desc = gcal_item['description']
        # strip whitespaces, empty lines
        lines = [l.strip() for l in gcal_desc.split('\n') if l][1:]

        # annotations
        i = 0
        for i, l in enumerate(lines):
            parts = l.split(':', maxsplit=1)
            if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
                annotations.append(parts[1].strip())
            else:
                break

        if i == len(lines) - 1:
            return annotations, status, uuid

        # Iterate through rest of lines, find only the status and uuid ones
        for l in lines[i:]:
            parts = l.split(':', maxsplit=1)
            if len(parts) == 2:
                start = parts[0].lower()
                if start.startswith("* status"):
                    status = parts[1].strip().lower()
                elif start.startswith("* uuid"):
                    try:
                        uuid = UUID(parts[1].strip())
                    except ValueError as err:
                        logger.error("Invalid UUID %s provided during GCal -> TW conversion, Using None..."
                                     % err)

        return annotations, status, uuid

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
