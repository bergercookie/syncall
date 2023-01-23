import datetime
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Union, cast

import dateutil
import pkg_resources
import pytz
from bubop import format_datetime_tz, logger
from googleapiclient import discovery
from googleapiclient.http import HttpError

from syncall.google.google_side import GoogleSide
from syncall.sync_side import SyncSide

DEFAULT_CLIENT_SECRET = pkg_resources.resource_filename(
    "syncall", os.path.join("res", "gcal_client_secret.json")
)


class GCalSide(GoogleSide):
    """GCalSide interacts with the Google Calendar API.


    Adds, removes, and updates events on Google Calendar. Also handles the
    OAuth2 user authentication workflow.
    """

    ID_KEY = "id"
    SUMMARY_KEY = "summary"
    LAST_MODIFICATION_KEY = "updated"
    _identical_comparison_keys = [
        "description",
        "end",
        "start",
        "summary",
    ]

    _date_keys = ["end", "start", "updated"]
    _date_format = "%Y-%m-%d"

    def __init__(
        self,
        *,
        calendar_summary="TaskWarrior Reminders",
        client_secret,
        **kargs,
    ):
        if client_secret is None:
            client_secret = DEFAULT_CLIENT_SECRET

        super().__init__(
            name="Gcal",
            fullname="Google Calendar",
            scopes=["https://www.googleapis.com/auth/calendar"],
            credentials_cache=Path.home() / ".gcal_credentials.pickle",
            client_secret=client_secret,
            **kargs,
        )

        self._calendar_summary = calendar_summary
        self._calendar_id = None
        self._items_cache: Dict[str, dict] = {}

    def start(self):
        logger.debug("Connecting to Google Calendar...")
        creds = self._get_credentials()
        self._service = discovery.build("calendar", "v3", credentials=creds)
        self._calendar_id = self._fetch_cal_id()

        # Create calendar if not there --------------------------------------------------------
        if self._calendar_id is None:
            logger.info(f"Creating calendar {self._calendar_summary}")
            new_cal = {"summary": self._calendar_summary}
            ret = self._service.calendars().insert(body=new_cal).execute()  # type: ignore
            assert "id" in ret
            new_cal_id = ret["id"]
            logger.info(f"Created calendar, id: {new_cal_id}")
            self._calendar_id = new_cal_id

        logger.debug("Connected to Google Calendar.")

    def _fetch_cal_id(self) -> Optional[str]:
        """Return the id of the Calendar based on the given Summary.

        :returns: id or None if that was not found
        """
        res = self._service.calendarList().list().execute()  # type: ignore
        calendars_list: List[dict] = res["items"]

        matching_calendars = [
            c["id"] for c in calendars_list if c["summary"] == self._calendar_summary
        ]

        if len(matching_calendars) == 0:
            return None
        elif len(matching_calendars) == 1:
            return cast(str, matching_calendars[0])
        else:
            raise RuntimeError(
                f'Multiple matching calendars for name -> "{self._calendar_summary}"'
            )

    def _clear_all_calendar_entries(self):
        """Clear all events from the current calendar."""
        # TODO Currently not functional - returning "400 Bad Request"
        logger.warning(f"Clearing all events from calendar {self._calendar_id}")
        self._service.calendars().clear(calendarId=self._calendar_id).execute()

    def get_all_items(self, **kargs):
        """Get all the events for the calendar that we use.

        :param kargs: Extra options for the call
        """
        # Get the ID of the calendar of interest
        events = []
        request = self._service.events().list(calendarId=self._calendar_id)

        # Loop until all pages have been processed.
        while request is not None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            events.extend([e for e in response.get("items", []) if e["status"] != "cancelled"])

            # Get the next request object by passing the previous request
            # object to the list_next method.
            request = self._service.events().list_next(request, response)

        # cache them
        for e in events:
            self._items_cache[e["id"]] = e

        return events

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[dict]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self._get_item_refresh(item_id=item_id)

        return item

    def _get_item_refresh(self, item_id: str) -> Optional[dict]:
        ret = None
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

    @classmethod
    def last_modification_key(cls) -> str:
        return cls.LAST_MODIFICATION_KEY

    @staticmethod
    def get_date_key(d: dict) -> Union[Literal["date"], Literal["dateTime"]]:
        """Get key corresponding to the date field."""
        if "dateTime" not in d.keys() and "date" not in d.keys():
            raise RuntimeError("None of the required keys is in the dictionary")

        return "date" if d.get("date", None) else "dateTime"

    @staticmethod
    def get_event_time(item: dict, t: str) -> datetime.datetime:
        """
        Return the start/end datetime in datetime format.

        :param t: Time to query, 'start' or 'end'
        """
        assert t in ["start", "end"]
        assert t in item.keys(), "'end' key not found in item"

        # sometimes the google calendar api returns this as a datetime
        if isinstance(item[t], datetime.datetime):
            return item[t]

        dt = GCalSide.parse_datetime(item[t][GCalSide.get_date_key(item[t])])
        return dt

    @staticmethod
    def format_datetime(dt: datetime.datetime) -> str:
        assert isinstance(dt, datetime.datetime)
        return format_datetime_tz(dt)

    @classmethod
    def parse_datetime(cls, dt: Union[str, dict, datetime.datetime]) -> datetime.datetime:
        """
        Parse datetime given in the GCal format(s):
        - string with ('T', 'Z' separators).
        - (dateTime, dateZone) dictionary
        - datetime object

        Usage::

        >>> GCalSide.parse_datetime("2019-03-05T00:03:09Z")
        datetime.datetime(2019, 3, 5, 0, 3, 9)
        >>> GCalSide.parse_datetime("2019-03-05")
        datetime.datetime(2019, 3, 5, 0, 0)
        >>> GCalSide.parse_datetime("2019-03-05T00:03:01.1234Z")
        datetime.datetime(2019, 3, 5, 0, 3, 1, 123400)
        >>> GCalSide.parse_datetime("2019-03-08T00:29:06.602Z")
        datetime.datetime(2019, 3, 8, 0, 29, 6, 602000)

        >>> from tzlocal import get_localzone_name
        >>> tz = get_localzone_name()
        >>> a = GCalSide.parse_datetime({"dateTime": "2021-11-14T22:07:49Z", "timeZone": tz})
        >>> b = GCalSide.parse_datetime({"dateTime": "2021-11-14T22:07:49.000000Z"})
        >>> b
        datetime.datetime(2021, 11, 14, 22, 7, 49)
        >>> from bubop.time import is_same_datetime
        >>> is_same_datetime(a, b) or (print(a) or print(b))
        True
        >>> GCalSide.parse_datetime({"dateTime": "2021-11-14T22:07:49.123456"})
        datetime.datetime(2021, 11, 14, 22, 7, 49, 123456)
        >>> a = GCalSide.parse_datetime({"dateTime": "2021-11-14T22:07:49Z", "timeZone": tz})
        >>> GCalSide.parse_datetime(a).isoformat() == a.isoformat()
        True
        """

        if isinstance(dt, str):
            return dateutil.parser.parse(dt).replace(tzinfo=None)  # type: ignore
        elif isinstance(dt, dict):
            date_time = dt.get("dateTime")
            if date_time is None:
                raise RuntimeError(f"Invalid structure dict: {dt}")
            dt_dt = GCalSide.parse_datetime(date_time)
            time_zone = dt.get("timeZone")
            if time_zone is not None:
                timezone = pytz.timezone(time_zone)
                dt_dt = timezone.localize(dt_dt)

            return dt_dt
        elif isinstance(dt, datetime.datetime):
            return dt
        else:
            raise RuntimeError(
                f"Unexpected type of a given date item, type: {type(dt)}, contents: {dt}"
            )

    @classmethod
    def items_are_identical(cls, item1, item2, ignore_keys: Sequence[str] = []) -> bool:
        for item in [item1, item2]:
            for key in cls._date_keys:
                if key not in item:
                    continue

                item[key] = cls.parse_datetime(item[key])

        return SyncSide._items_are_identical(
            item1,
            item2,
            keys=[k for k in cls._identical_comparison_keys if k not in ignore_keys],
        )
