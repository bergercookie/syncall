from typing import Dict, Sequence

import caldav
from bubop import logger
from item_synchronizer.types import ID

from taskwarrior_syncall.sync_side import SyncSide
from taskwarrior_syncall.tw_caldav_utils import map_ics_to_item


class CaldavSide(SyncSide):
    """
    Wrapper to add/modify/delete todo entries from a caldav server
    """

    ID_KEY = "id"
    SUMMARY_KEY = "summary"
    LAST_MODIFICATION_KEY = "last-modified"
    _identical_comparison_keys = [
        "description",
        "end",
        "start",
        "summary",
    ]

    _date_keys = ["end", "start", "last-modified"]
    _date_format = "%Y-%m-%d"

    def __init__(self, client: caldav.DAVClient, calendar_name: str) -> None:
        super().__init__(name="caldav", fullname="Caldav")

        self._client = client.principal()
        self._calendar_name = calendar_name
        self._calendar = None
        self._items_cache: Dict[str, dict] = {}

    def start(self):
        logger.info(f"Initializing {self.fullname}...")
        self._calendar = self._get_calendar()
        logger.debug(f"Connected to calendar - {self._calendar.name}")

    def _get_calendar(self) -> caldav.DAVClient.calendar:
        try:
            calendar = self._client.calendar(name=self._calendar_name)
            logger.debug(f"Connected to calendar {calendar.name}")
            acceptable_component_types = calendar.get_supported_components()
            if "VTODO" not in acceptable_component_types:
                raise RuntimeError(
                    f"Calendar {self._calendar_name} found but does not support VTODO entries"
                    " - please choose a different calendar"
                )
        except caldav.error.NotFoundError:
            # Create calendar if not there -------------------------------------------------
            logger.info(f"Calendar not found = Creating new calendar {self._calendar_name}")
            calendar = self._client.make_calendar(
                name=self._calendar_name, supported_calendar_component_set=["VTODO"]
            )
        return calendar

    def get_all_items(self, **kargs):
        todos = []
        raw_todos = self._calendar.todos()

        # Format & cache items from ics files
        for t in raw_todos:
            data = t.icalendar_component
            item = map_ics_to_item(data)
            todos.append(item)
            self._items_cache[item["id"]] = item

        return todos

    def get_item(self, item_id: ID, use_cached: bool = False):
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self._find_todo_by_id(item_id=item_id)
        return item

    def _find_todo_by_id(self, item_id: ID, raw: bool = False):
        item = next(
            (
                item
                for item in self._calendar.todos()
                if item.icalendar_component.get("uid") == item_id
            ),
            None,
        )
        if item and not raw:
            item = map_ics_to_item(item.icalendar_component)
        return item

    def delete_single_item(self, item_id: ID):
        todo = self._find_todo_by_id(item_id=item_id, raw=True)
        if todo:
            todo.delete()

    def update_item(self, item_id: ID, **changes):
        todo = self._find_todo_by_id(item_id=item_id)
        for key, value in changes.items():
            todo.icalendar_component[key] = value
        todo.save()

    def add_item(self, item):
        todo = self._calendar.add_todo(
            summary=item.get("summary"),
            priority=item.get("priority"),
            description=item.get("description"),
            status=item.get("status").upper(),
            due=item.get("due"),
        )
        return map_ics_to_item(todo.icalendar_component)

    @classmethod
    def id_key(cls) -> str:
        return cls.ID_KEY

    @classmethod
    def summary_key(cls) -> str:
        return cls.SUMMARY_KEY

    @classmethod
    def last_modification_key(cls) -> str:
        return cls.LAST_MODIFICATION_KEY

    @classmethod
    def items_are_identical(cls, item1, item2, ignore_keys: Sequence[str] = []) -> bool:
        return SyncSide._items_are_identical(
            item1,
            item2,
            keys=[k for k in cls._identical_comparison_keys if k not in ignore_keys],
        )
