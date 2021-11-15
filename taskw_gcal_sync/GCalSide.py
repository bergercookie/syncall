import datetime
import os
import pickle
from pathlib import Path
from typing import Dict, Literal, Optional, Union

import dateutil
import pkg_resources
import pytz
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery
from googleapiclient.http import HttpError

from taskw_gcal_sync.GenericSide import GenericSide
from taskw_gcal_sync.logger import logger


class GCalSide(GenericSide):
    """GCalSide interacts with the Google Calendar API.


    Adds, removes, and updates events on Google Calendar. Also handles the
    OAuth2 user authentication workflow.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    _datetime_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    _date_format = "%Y-%m-%d"

    def __init__(self, *, oauth_port: int, **kargs):
        super().__init__()

        # set the default properties
        self.config = {
            "calendar_summary": "TaskWarrior Reminders",
            "credentials_cache": Path.home() / ".gcal_credentials.pickle",
            "client_secret": pkg_resources.resource_filename(
                __name__, os.path.join("res", "gcal_client_secret.json")
            ),
        }

        self._default_client_secret: str = self.config["client_secret"]
        self.config.update(kargs)

        self._oauth_port = oauth_port
        self._calendar_id = None
        self._items_cache: Dict[str, dict] = {}

        self._identical_comparison_keys = [
            "description",
            "end",
            "start",
            "summary",
            "updated",
        ]

        self._date_keys = ["end", "start", "updated"]

        # If you modify this, delete your previously saved credentials
        self.service = None

    def start(self):
        logger.debug("Connecting to Google Calendar...")
        self.gain_access()
        self._calendar_id = self._fetch_cal_id()

        # Create calendar if not there --------------------------------------------------------
        if self._calendar_id is None:
            logger.info(f'Creating calendar {self.config["calendar_summary"]}')
            new_cal = {"summary": self.config["calendar_summary"]}
            ret = self.service.calendars().insert(body=new_cal).execute()  # type: ignore
            new_cal_id = ret["id"]
            logger.info(f"Created calendar, id: {new_cal_id}")
            self._calendar_id = new_cal_id

        logger.debug("Connected to Google Calendar.")

    def _fetch_cal_id(self) -> Optional[str]:
        """Return the id of the Calendar based on the given Summary.

        :returns: id or None if that was not found
        """
        res = self.service.calendarList().list().execute()  # type: ignore
        calendars_list = res.get("items", None)  # list(dict)
        assert calendars_list and isinstance(calendars_list, list)

        matching_calendars = [
            c["id"] for c in calendars_list if c["summary"] == self.config["calendar_summary"]
        ]

        if len(matching_calendars) == 0:
            return None
        elif len(matching_calendars) == 1:
            return matching_calendars[0]
        else:
            raise RuntimeError(
                f'Multiple matching calendars for name -> "{self.config["calendar_summary"]}"'
            )

    def _clear_all_calendar_entries(self):
        """Clear all events from the current calendar."""
        # TODO Currently not functional - returning "400 Bad Request"
        logger.warning(f"Clearing all events from calendar {self._calendar_id}")
        self.service.calendars().clear(calendarId=self._calendar_id).execute()

    def get_all_items(self, **kargs):
        """Get all the events for the calendar that we use.

        :param kargs: Extra options for the call
        """
        # Get the ID of the calendar of interest
        events = []
        request = self.service.events().list(calendarId=self._calendar_id)

        # Loop until all pages have been processed.
        while request is not None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            events.extend([e for e in response.get("items", []) if e["status"] != "cancelled"])

            # Get the next request object by passing the previous request
            # object to the list_next method.
            request = self.service.events().list_next(request, response)

        # cache them
        for e in events:
            self._items_cache[e["id"]] = e

        return events

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[dict]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self.get_item_refresh(item_id=item_id)

        return item

    def get_item_refresh(self, item_id: str) -> Optional[dict]:
        ret = None
        try:
            ret = (
                self.service.events()
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
            self.service.events().get(calendarId=self._calendar_id, eventId=item_id).execute()
        )
        event.update(changes)
        self.service.events().update(
            calendarId=self._calendar_id, eventId=event["id"], body=event
        ).execute()

    def add_item(self, item) -> dict:
        event = self.service.events().insert(calendarId=self._calendar_id, body=item).execute()
        logger.debug(f'Event created -> {event.get("htmlLink")}')

        return event

    def delete_single_item(self, item_id) -> None:
        self.service.events().delete(calendarId=self._calendar_id, eventId=item_id).execute()

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        :return: Credentials, the obtained credentials.
        """

        creds = None
        credentials_cache = self.config["credentials_cache"]
        if credentials_cache.is_file():
            with credentials_cache.open("rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            logger.info("Invalid credentials. Fetching again...")
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secret = self.config["client_secret"]
                if client_secret != self._default_client_secret:
                    logger.info(f"Using custom client secret -> {client_secret}")
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret, GCalSide.SCOPES
                )
                try:
                    creds = flow.run_local_server(port=self._oauth_port)
                except OSError:
                    raise RuntimeError(
                        f"Port {self._oauth_port} is already in use, please specify a"
                        " different port or stop the process that's already using it."
                    )

            # Save the credentials for the next run
            with credentials_cache.open("wb") as f:
                pickle.dump(creds, f)
        else:
            logger.info("Using already cached credentials...")

        return creds

    def gain_access(self):
        creds = self._get_credentials()
        self.service = discovery.build("calendar", "v3", credentials=creds)

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

        dt = GCalSide.parse_datetime(item[t][GCalSide.get_date_key(item[t])])
        return dt

    @staticmethod
    def format_datetime(dt: datetime.datetime) -> str:
        """
        Format a datetime object according to the ISO speicifications containing
        the 'T' and 'Z' separators

        Usage::

        >>> GCalSide.format_datetime(datetime.datetime(2019, 3, 5, 0, 3, 9, 1234))
        '2019-03-05T00:03:09.001234Z'
        >>> GCalSide.format_datetime(datetime.datetime(2019, 3, 5, 0, 3, 9, 123))
        '2019-03-05T00:03:09.000123Z'
        """

        assert isinstance(dt, datetime.datetime)
        dt_out = dt.strftime(GCalSide._datetime_format)
        return dt_out

    @staticmethod
    def parse_datetime(dt: Union[str, dict, datetime.datetime]) -> datetime.datetime:
        """
        Parse datetime given in the GCal format(s):
        - string with ('T', 'Z' separators).
        - (dateTime, dateZone) dictionary
        - datetime object

        Usage::

        >>> GCalSide.parse_datetime('2019-03-05T00:03:09Z')
        datetime.datetime(2019, 3, 5, 0, 3, 9)
        >>> GCalSide.parse_datetime('2019-03-05')
        datetime.datetime(2019, 3, 5, 0, 0)
        >>> GCalSide.parse_datetime('2019-03-05T00:03:01.1234Z')
        datetime.datetime(2019, 3, 5, 0, 3, 1, 123400)
        >>> GCalSide.parse_datetime('2019-03-08T00:29:06.602Z')
        datetime.datetime(2019, 3, 8, 0, 29, 6, 602000)

        >>> a = GCalSide.parse_datetime({'dateTime': '2021-11-14T22:07:49Z', 'timeZone': 'UTC'})
        >>> b = GCalSide.parse_datetime({'dateTime': '2021-11-14T22:07:49.000000Z'})
        >>> b
        datetime.datetime(2021, 11, 14, 22, 7, 49)
        >>> from taskw_gcal_sync.helpers import is_same_datetime
        >>> is_same_datetime(a, b)
        True
        >>> GCalSide.parse_datetime({'dateTime': '2021-11-14T22:07:49.123456'})
        datetime.datetime(2021, 11, 14, 22, 7, 49, 123456)
        >>> a = GCalSide.parse_datetime({'dateTime': '2021-11-14T22:07:49Z', 'timeZone': 'UTC'})
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

    def items_are_identical(self, item1, item2, ignore_keys=None) -> bool:
        ignore_keys_ = ignore_keys if ignore_keys is not None else []
        for item in [item1, item2]:
            for key in self._date_keys:
                if key not in item:
                    continue

                item[key] = self.parse_datetime(item[key])

        return GenericSide._items_are_identical(
            item1,
            item2,
            keys=[k for k in self._identical_comparison_keys if k not in ignore_keys_],
        )
