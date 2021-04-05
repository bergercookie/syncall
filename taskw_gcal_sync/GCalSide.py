import datetime
import os
import pickle
from typing import Union

import dateutil
import pkg_resources
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import discovery
from googleapiclient.http import HttpError
from overrides import overrides

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

    def __init__(self, **kargs):
        super(GCalSide, self).__init__()

        # set the default properties
        self.config = {
            "calendar_summary": "TaskWarrior Reminders",
            "calendar_id": None,
            "client_secret_file": pkg_resources.resource_filename(
                "taskw_gcal_sync", os.path.join("res", "gcal_client_secret.json")
            ),
            "credentials_cache": os.path.join(
                os.path.expanduser("~"), ".gcal_credentials.pickle"
            ),
        }
        self.config.update(kargs)

        # If you modify this, delete your previously saved credentials
        self.service = None

    @overrides
    def start(self):
        # connect
        logger.info("Connecting...")
        self.gain_access()
        self.config["calendar_id"] = self._fetch_cal_id()
        # Create calendar if not there
        if not self.config["calendar_id"]:
            logger.info('Creating calendar "%s"' % self.config["calendar_summary"])
            new_cal = {"summary": self.config["calendar_summary"]}
            ret = self.service.calendars().insert(body=new_cal).execute()  # type: ignore
            logger.info("Created, id: %s" % ret["id"])
            self.config["calendar_id"] = ret["id"]
        logger.info("Connected.")

    def _fetch_cal_id(self):
        """Return the id of the Calendar based on the given Summary.

        :returns: id or None if that was not found
        """
        res = self.service.calendarList().list().execute()  # type: ignore
        calendars_list = res.get("items", None)  # list(dict)
        assert calendars_list and isinstance(calendars_list, list)

        matching_calendars = [
            c["id"] for c in calendars_list if c["summary"] == self.config["calendar_summary"]
        ]

        if matching_calendars:
            assert len(matching_calendars) == 1, "Too many calendars match!"
            ret = matching_calendars[0]
        else:
            ret = None
        return ret

    @overrides
    def get_all_items(self, **kargs):
        """Get all the events for the calendar that we use.

        :param kargs: Extra options for the call
        """
        # Get the ID of the calendar of interest

        if kargs:
            logger.warning(
                "Extra arguments in get_all_items call are not supported yet, ignoring them: {}".format(
                    kargs
                )
            )

        events = []
        request = self.service.events().list(calendarId=self.config["calendar_id"])

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

        return events

    @overrides
    def get_single_item(self, _id: str) -> Union[dict, None]:
        ret = None
        try:
            ret = (
                self.service.events()
                .get(calendarId=self.config["calendar_id"], eventId=_id)
                .execute()
            )
            if ret["status"] == "cancelled":
                ret = None
        except HttpError:
            pass
        finally:
            return ret

    @overrides
    def update_item(self, item_id, **changes):
        GCalSide._sanitize_all_datetimes(changes)

        # Check if item is there
        event = (
            self.service.events()
            .get(calendarId=self.config["calendar_id"], eventId=item_id)
            .execute()
        )
        event.update(changes)
        self.service.events().update(
            calendarId=self.config["calendar_id"], eventId=event["id"], body=event
        ).execute()

    @overrides
    def add_item(self, item) -> dict:
        GCalSide._sanitize_all_datetimes(item)
        event = (
            self.service.events()
            .insert(calendarId=self.config["calendar_id"], body=item)
            .execute()
        )
        logger.debug('Event created: "%s"' % event.get("htmlLink"))

        return event

    @overrides
    def delete_single_item(self, item_id) -> None:
        self.service.events().delete(
            calendarId=self.config["calendar_id"], eventId=item_id
        ).execute()

    def _get_credentials_file(self):
        """Return the path to the credentials file.

        Useful method for running this script from an arbitrary dir.
        """
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_dir, self.config["client_secret_file"])

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        :return: Credentials, the obtained credentials.
        """

        creds = None
        credentials_cache = self.config["credentials_cache"]
        if os.path.isfile(credentials_cache):
            with open(credentials_cache, "rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            logger.info("Invalid credentials. Fetching them...")
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secret = pkg_resources.resource_filename(
                    __name__, os.path.join("res", "gcal_client_secret.json")
                )
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret, GCalSide.SCOPES
                )
                creds = flow.run_local_server()
            # Save the credentials for the next run
            with open(credentials_cache, "wb") as token:
                pickle.dump(creds, token)
        else:
            logger.info("Using already cached credentials...")

        return creds

    def gain_access(self):
        creds = self._get_credentials()
        self.service = discovery.build("calendar", "v3", credentials=creds)

    @staticmethod
    def get_date_key(d: dict) -> str:
        """
        Get key corresponding to date -> 'date' or 'dateTime'
        """
        assert (
            "dateTime" in d.keys() or "date" in d.keys()
        ), "None of the required keys is in the dictionary"
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
    def parse_datetime(dt: str) -> datetime.datetime:
        """
        Parse datetime given in the GCal format ('T', 'Z' separators).

        Usage::

        >>> GCalSide.parse_datetime('2019-03-05T00:03:09Z')
        datetime.datetime(2019, 3, 5, 0, 3, 9)
        >>> GCalSide.parse_datetime('2019-03-05')
        datetime.datetime(2019, 3, 5, 0, 0)
        >>> GCalSide.parse_datetime('2019-03-05T00:03:01.1234Z')
        datetime.datetime(2019, 3, 5, 0, 3, 1, 123400)
        >>> GCalSide.parse_datetime('2019-03-08T00:29:06.602Z')
        datetime.datetime(2019, 3, 8, 0, 29, 6, 602000)
        """

        assert isinstance(dt, str)
        return dateutil.parser.parse(dt).replace(tzinfo=None)

    @staticmethod
    def _sanitize_all_datetimes(item: dict) -> None:
        item["updated"] = GCalSide.sanitize_datetime(item["updated"])
        if "dateTime" in item["start"]:
            item["start"]["dateTime"] = GCalSide.sanitize_datetime(item["start"]["dateTime"])
        if "dateTime" in item["end"]:
            item["end"]["dateTime"] = GCalSide.sanitize_datetime(item["end"]["dateTime"])

    @staticmethod
    def sanitize_datetime(dt: str) -> str:
        """Given a date in str, make sure that the HH:MM:SS is not 00:00:00.

        >>> GCalSide.sanitize_datetime('2019-03-08T00:00:00.602Z')
        '2019-03-07T23:59:00.602000Z'
        >>> GCalSide.sanitize_datetime('2019-03-08T00:00:00.0000Z')
        '2019-03-07T23:59:00.000000Z'
        >>> GCalSide.sanitize_datetime('2019-03-08T00:29:06.602Z')
        '2019-03-08T00:29:06.602000Z'
        """

        dt_dt = GCalSide.parse_datetime(dt)
        if dt_dt.hour == 0 and dt_dt.minute == 0 and dt_dt.second == 0:
            dt_dt -= datetime.timedelta(minutes=1)

        return GCalSide.format_datetime(dt_dt)

    @staticmethod
    def items_are_identical(item1, item2, ignore_keys=[]) -> bool:

        keys = [
            k
            for k in [
                "created",
                "creator",
                "description",
                "end",
                "etag",
                "htmlLlink",
                "iCalUID",
                "kind",
                "organizer",
                "start",
                "summary",
                "updated",
            ]
            if k not in ignore_keys
        ]

        return GenericSide._items_are_identical(item1, item2, keys=keys)
