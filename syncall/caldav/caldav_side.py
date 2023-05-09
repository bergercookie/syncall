from typing import Any, Dict, Optional, Sequence

import caldav
from bubop import logger
from caldav.lib.error import NotFoundError
from icalendar.prop import vCategory, vDatetime, vText
from item_synchronizer.types import ID

from syncall.app_utils import error_and_exit
from syncall.caldav.caldav_utils import calendar_todos, icalendar_component, map_ics_to_item
from syncall.sync_side import SyncSide


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
        "status",
        "summary",
        "due",
    ]

    _date_keys = ["end", "start", "last-modified"]

    def __init__(self, client: caldav.DAVClient, calendar_name: str) -> None:
        super().__init__(name="caldav", fullname="Caldav")

        self._client = client.principal()
        self._calendar_name = calendar_name
        self._calendar: caldav.Calendar
        self._items_cache: Dict[str, dict] = {}

    def start(self):
        logger.info(f"Initializing {self.fullname}...")
        self._calendar = self._get_calendar()
        logger.debug(f"Connected to calendar - {self._calendar.name}")

    def _get_calendar(self) -> caldav.Calendar:
        try:
            calendar = self._client.calendar(name=self._calendar_name)
            logger.debug(f"Connected to calendar {calendar.name}")
            acceptable_component_types = calendar.get_supported_components()
            if "VTODO" not in acceptable_component_types:
                error_and_exit(
                    f"Calendar {self._calendar_name} found but does not support VTODO entries"
                    " - please choose a different calendar"
                )
        except NotFoundError:
            # Create calendar if not there -------------------------------------------------
            logger.info(f"Calendar not found = Creating new calendar {self._calendar_name}")
            calendar = self._client.make_calendar(
                name=self._calendar_name, supported_calendar_component_set=["VTODO"]
            )
        return calendar

    def get_all_items(self, **kargs):
        todos = []
        raw_todos = calendar_todos(self._calendar)

        # Format & cache items from ics files
        for t in raw_todos:
            data = icalendar_component(t)
            item = map_ics_to_item(data)
            todos.append(item)
            self._items_cache[item["id"]] = item

        return todos

    def get_item(self, item_id: ID, use_cached: bool = False):
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self._find_todo_by_id(item_id=item_id)
        return item

    def _find_todo_by_id_raw(self, item_id: ID) -> Optional[caldav.CalendarObjectResource]:
        item = next(
            (
                item
                for item in calendar_todos(self._calendar)
                if icalendar_component(item).get("uid") == item_id
            ),
            None,
        )

        return item

    def _find_todo_by_id(self, item_id: ID) -> Optional[Dict]:
        raw_item = self._find_todo_by_id_raw(item_id=item_id)
        if raw_item:
            return map_ics_to_item(icalendar_component(raw_item))

    def delete_single_item(self, item_id: ID):
        todo = self._find_todo_by_id_raw(item_id=item_id)
        if todo is not None:
            todo.delete()

    def update_item(self, item_id: ID, **changes):
        todo = self._find_todo_by_id_raw(item_id=item_id)
        if todo is None:
            logger.error(
                f"Trying to update item but cannot find item on the CalDav server -> {item_id}"
            )
            logger.opt(lazy=True).debug(f"Can't update item {item_id}\n\nchanges: {changes}")
            return

        def set_(key: str, val: Any):
            icalendar_component(todo)[key] = val

        # pop the key:value (s) that we're intending to potentially update
        for key in self._identical_comparison_keys:
            icalendar_component(todo).pop(key)

        for key, value in changes.items():
            if key == "status":
                set_(key, vText(value.upper()))
            if key in ["due", "created", "last-modified"]:
                set_(key, vDatetime(value))
            if key in ["priority", "description", "summary"]:
                set_(key, vText(value))
            if key == "categories":
                set_(key, vCategory([vText(cat) for cat in value]))

        todo.save()

    def add_item(self, item):
        todo = self._calendar.add_todo(
            summary=item.get("summary"),
            priority=item.get("priority"),
            description=item.get("description"),
            status=item.get("status").upper(),
            due=item.get("due"),
            categories=item.get("categories"),
            created=item.get("created"),
            completed=item.get("completed"),
        )
        return map_ics_to_item(icalendar_component(todo))

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
