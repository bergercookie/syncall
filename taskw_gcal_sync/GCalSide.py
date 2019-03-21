from taskw_gcal_sync import GenericSide

from googleapiclient.http import HttpError
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import httplib2
import os
import datetime
from typing import Any, Dict, Union
import re

class GCalSide(GenericSide):
    """GCalSide interacts with the Google Calendar API.


    Adds, removes, and updates events on Google Calendar. Also handles the
    OAuth2 user authentication workflow.
    """

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    _datetime_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    _date_format = "%Y-%m-%d"

    def __init__(self, **kargs):
        super(GCalSide, self).__init__()

        # set the default properties
        self.config = {
            'calendar_summary': 'TaskWarrior Reminders',
            'calendar_id': None,
            'app_name': 'Google Calendar Sync',
            'client_secret_file': os.path.join(os.path.expanduser('~'),
                                               '.gcal_client_secret.json'),
            'credentials_dir': os.path.join(os.path.expanduser('~'),
                                            '.gcal_credentials'),
            'credentials_fname': 'gcal_sync.json',
        }
        self.config.update(kargs)

        # If you modify this, delete your previously saved credentials
        self.service = None

    def start(self):
        # connect
        self.logger.info("Connecting...")
        self.gain_access()
        self.config['calendar_id'] = \
            self._fetch_cal_id_from_summary(self.config["calendar_summary"])
        # Create calendar if not there
        if not self.config['calendar_id']:
            self.logger.info("Creating calendar \"%s\""
                             % self.config["calendar_summary"])
            new_cal = {
                'summary': self.config["calendar_summary"]
            }
            ret = self.service.calendars().insert(body=new_cal).execute()
            self.logger.info("Created, id: %s" % ret["id"])
            self.config['calendar_id'] = ret["id"]
        self.logger.info("Connected.")

    def _get_credentials_file(self):
        """Return the path to the credentials file.

        Useful method for running this script from an arbitrary dir.
        """
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_dir, self.config['client_secret_file'])

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if not os.path.isdir(self.config['credentials_dir']):
            os.makedirs(self.config['credentials_dir'])
        credentials_path = os.path.join(self.config['credentials_dir'],
                                        self.config['credentials_fname'])

        store = Storage(credentials_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            self.logger.info('Credentials not there. Fetching them...')
            flow = client.flow_from_clientsecrets(
                self._get_credentials_file(), GCalSide.SCOPES)
            flow.user_agent = self.config['app_name']
            credentials = tools.run_flow(flow, store)
            self.logger.info('Storing credentials in %s' % credentials_path)
        else:
            self.logger.info('Using already cached credentials...')
        return credentials

    def _fetch_cal_id_from_summary(self, cal_summary: str):
        """Return the id of the Calendar based on the given Summary.

        :returns: id or None if that was not found
        """
        res = self.service.calendarList().list().execute()
        calendars_list = res.get('items', None)  # list(dict)
        assert calendars_list and isinstance(calendars_list, list)

        matching_calendars = [c['id'] for c in calendars_list
                              if c['summary'] == self.config['calendar_summary']]

        if matching_calendars:
            assert len(matching_calendars) == 1 and "Too many calendars match!"
            ret = matching_calendars[0]
        else:
            ret = None
        return ret

    def get_all_items(self, **kargs):
        """Get all the events for the calendar that we use.

        :param kargs: Extra options for the call
        """
        # Get the ID of the calendar of interest

        events = []
        request = self.service.events().list(calendarId=self.config['calendar_id'])

        # Loop until all pages have been processed.
        while request is not None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            for event in response.get('items', []):
                events.append(event)

            # Get the next request object by passing the previous request
            # object to the list_next method.
            request = self.service.events().list_next(request, response)

        return events

    def get_single_item(self, _id: str) -> Union[dict, None]:
        try:
            return self.service.events().get(
                calendarId=self.config['calendar_id'],
                eventId=_id).execute()
        except HttpError:
            return None

    def update_item(self, item_id: str, **changes):
        GCalSide._sanitize_all_datetimes(changes)

        # Check if item is there
        event = self.service.events().get(
            calendarId=self.config["calendar_id"],
            eventId=item_id).execute()
        event.update(changes)
        self.service.events().update(
            calendarId=self.config["calendar_id"],
            eventId=event['id'], body=event).execute()

    def add_item(self, item) -> dict:
        GCalSide._sanitize_all_datetimes(item)
        event = self.service.events().insert(
            calendarId=self.config["calendar_id"],
            body=item).execute()
        self.logger.debug('Event created: \"%s\"' % event.get('htmlLink'))

        return event

    def gain_access(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)

    @staticmethod
    def get_date_key(d: dict) -> str:
        """
        Get key corresponding to date -> 'date' or 'dateTime'
        """
        assert len(d) == 1, "Input dictionary contains more than 1 key"
        assert 'dateTime' in d.keys() or 'date' in d.keys(), \
            "None of the required keys is in the dictionary"
        return 'date' if d.get('date', None) else 'dateTime'

    @staticmethod
    def get_event_time(item: dict, t: str) -> datetime.datetime:
        """
        Return the start/end datetime in datetime format.

        :param t: Time to query, 'start' or 'end'
        """
        assert t in ['start', 'end']
        assert t in item.keys(), "'end' key not found in item"
        dt = GCalSide.parse_datetime(
            item[t][GCalSide.get_date_key(item[t])])
        return dt

    @staticmethod
    def format_datetime(dt: datetime.datetime) -> str:
        """
        Format a datetime object to the ISO speicifications containing the 'T'
        and 'Z' separators

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
        dt2 = dt
        if 'T' in dt:
            # Adjust for microseconds
            g = re.match(".*:\d\d\.(\d*)Z$", dt)
            if g is None or not g.groups():
                dt2 = dt[:-1] + '.000000' + 'Z'
            elif len(g.groups()[0]) <= 6:
                dt2 = dt[:-1 - len(g.groups()[0])] \
                    + g.groups()[0] \
                    + '0' * (6 - len(g.groups()[0])) + 'Z'

            _format = GCalSide._datetime_format
        else:
            _format = GCalSide._date_format

        dt_out = datetime.datetime.strptime(dt2, _format)
        return dt_out

    @staticmethod
    def _sanitize_all_datetimes(item: dict) -> None:
        item['updated'] = GCalSide.sanitize_datetime(item['updated'])
        if 'dateTime' in item['start']:
            item['start']['dateTime'] = \
                GCalSide.sanitize_datetime(item['start']['dateTime'])
        if 'dateTime' in item['end']:
            item['end']['dateTime'] = \
                GCalSide.sanitize_datetime(item['end']['dateTime'])

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
            # dt_dt += datetime.timedelta(days=1)
            dt_dt -= datetime.timedelta(minutes=1)

        return GCalSide.format_datetime(dt_dt)

