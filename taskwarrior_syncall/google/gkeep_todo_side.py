import os
from pathlib import Path
from typing import Dict, Literal, Optional, Sequence, Union

from bubop import logger
from googleapiclient import discovery
from item_synchronizer.types import ID

from taskwarrior_syncall.sync_side import SyncSide


class GKeepTodoSide(SyncSide):
    """Integration for managing the todo checkboxes of Google Keep.

    Currently not using the official Google API since it's enterprise only.
    """

    ID_KEY = "TODO"
    SUMMARY_KEY = "summary"

    def __init__(
        self,
        **kargs,
    ):
        super().__init__(
            name="Gkeep",
            fullname="Google Keep",
            **kargs,
        )

        self._items_cache: Dict[str, dict] = {}

    def start(self):
        logger.debug("Connecting to Google Keep...")
        self._note_id = self._fetch_note_id()

        # Create note if not there ------------------------------------------------------------
        # TODO

        logger.debug("Connected to Google Keep.")

    def _fetch_note_id(self) -> Optional[str]:
        """Return the id of the Keep Note

        :returns: id or None if that was not found
        """
        # TODO
        pass

    def get_all_items(self, **kargs):
        """Get all the todo entries of the Notethat we use."""
        # TODO
        pass

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[dict]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self.get_item_refresh(item_id=item_id)

        return item

    def get_item_refresh(self, item_id: str) -> Optional[dict]:
        ret = None
        # TODO
        try:
            ret = (
                self._service.events()
                .get(calendarId=self._calendar_id, eventId=item_id)
                .execute()
            )
            if ret["status"] == "cancelled":
                ret = None
                self._items_cache.pop(item_id)
            else:
                self._items_cache[item_id] = ret
        except HttpError:
            pass
        finally:
            return ret

    def update_item(self, item_id, **changes):
        # Check if item is there
        event = (
            self._service.events().get(calendarId=self._calendar_id, eventId=item_id).execute()
        )
        event.update(changes)
        self._service.events().update(
            calendarId=self._calendar_id, eventId=event["id"], body=event
        ).execute()

    def add_item(self, item) -> dict:
        event = (
            self._service.events().insert(calendarId=self._calendar_id, body=item).execute()
        )
        logger.debug(f'Event created -> {event.get("htmlLink")}')

        return event

    def delete_single_item(self, item_id) -> None:
        self._service.events().delete(calendarId=self._calendar_id, eventId=item_id).execute()

    @classmethod
    def id_key(cls) -> str:
        return cls.ID_KEY

    @classmethod
    def summary_key(cls) -> str:
        return cls.SUMMARY_KEY

    @staticmethod
    def get_date_key(d: dict) -> Union[Literal["date"], Literal["dateTime"]]:
        """Get key corresponding to the date field."""
        if "dateTime" not in d.keys() and "date" not in d.keys():
            raise RuntimeError("None of the required keys is in the dictionary")

        return "date" if d.get("date", None) else "dateTime"

    @classmethod
    def items_are_identical(cls, item1, item2, ignore_keys: Sequence[ID] = []) -> bool:
        # TODO
        return True
