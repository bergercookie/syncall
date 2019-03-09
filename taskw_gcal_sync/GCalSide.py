from taskw_gcal_sync import GenericSide

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import httplib2
import os
import datetime

class GCalSide(GenericSide):
    """GCalSide interacts with the Google Calendar API.


    Adds, removes, and updates events on Google Calendar. Also handles the
    OAuth2 user authentication workflow.
    """

    SCOPES = 'https://www.googleapis.com/auth/calendar'
    datetime_format = "%Y-%m-%dT%H:%M:%SZ"

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
            'credentials_fname': os.path.join(os.path.expanduser('~'),
                                              'gcal_sync.json',)
        }
        self.config.update(kargs)

        # If you modify this, delete your previously saved credentials
        self.service = None

    def start(self):
        # connect
        self.logger.info("Connecting...")
        self.gain_access()
        self.logger.info("Connected.")

        # Create calendar if not there
        cal_id = self.fetch_cal_id_from_summary(self.config["calendar_summary"])
        if not cal_id:
            self.logger.info("Creating calendar \"%s\""
                             % self.config["calendar_summary"])
            new_cal = {
                'summary': self.config["calendar_summary"]
            }
            ret = self.service.calendars().insert(body=new_cal).execute()
            self.logger.info("Created, id: %s" % ret["id"])

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

    def fetch_cal_id_from_summary(self, cal_summary):
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

    def get_items(self):
        """Get all the events for the calendar that we use."""
        # Get the ID of the calendar of interest
        cal_id = self.fetch_cal_id_from_summary(cal_summary=self.config["calendar_summary"])

        events = []
        request = self.service.events().list(calendarId=cal_id)

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

    def update_item(self, item):
        super(GCalSide, self).update_item(item)
        raise NotImplementedError("TODO")

    def _add_item(self, item):
        super(GCalSide, self)._add_item(item)
        raise NotImplementedError("TODO")

    def gain_access(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        Format a datetime object to the ISO speicifications containing the 'T'
        and 'Z' separators

        >>> GCalSide.format_datetime(datetime.datetime(2019, 3, 5, 0, 3, 9))
        '2019-03-05T00:03:09Z'
        """
        return dt.strftime(GCalSide.datetime_format)

    @staticmethod
    def parse_datetime(dt: str) -> datetime.datetime:
        """
        Parse datetime given in the GCal foramt ('T', 'Z' separators)

        >>> GCalSide.parse_datetime('2019-03-05T00:03:09Z')
        datetime.datetime(2019, 3, 5, 0, 3, 9)
        """
        return datetime.datetime.strptime(dt, GCalSide.datetime_format)
