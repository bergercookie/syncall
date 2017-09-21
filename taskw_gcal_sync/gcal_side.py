from taskw_gcal_sync import GenericSide
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime, time
from rfc3339 import rfc3339

import logging
logger = logging.getLogger(__name__)


class GCalSide(GenericSide):
    """Current class handles the Google Calendar side. Due to limitations in
    the Python Google API, reminders are handled as a normal events calendar.
    """
    def __init__(self, **kargs):
        super(GCalSide, self).__init__()


        # set the default properties
        self.props = {
            'tw_cal_summary': 'TaskWarrior Reminders',
            'tw_cal_id': None,
            'client_secret_file': 'client_secret.json',
            'app_name': 'Google Calendar Sync',
            'credentials_dir': os.path.join(os.path.expanduser('~'),
                                            '.credentials'), # ~/.credentials
            'credentials_fname': 'gcal_sync.json',
        }
        self.props.update(kargs)


        # If you modify this, delete your previously saved credentials
        self.SCOPES = 'https://www.googleapis.com/auth/calendar'

        self.service = None
        self.gain_access()


    def _get_credentials_file(self):
        """Return the path to the credentials file.
        
        Useful method for running this script from an arbitrary dir.
        """
        script_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_dir, self.props['client_secret_file'])


    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        if not os.path.isdir(self.props['credentials_dir']):
            os.makedirs(self.props['credentials_dir'])
        credentials_path = os.path.join(self.props['credentials_dir'],
                                        self.props['credentials_fname'])

        store = Storage(credentials_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            logger.warn('Credentials not there. Fetching them...')
            flow = client.flow_from_clientsecrets(
                self._get_credentials_file(), self.SCOPES)
            flow.user_agent = self.props['app_name']
            credentials = tools.run_flow(flow, store)
            logger.warn('Storing credentials to ' + credentials_path)
        else:
            logger.warn('Using already cached credentials...')
        return credentials

    def fetch_cal_id_from_summary(self, cal_summary):
        res = self.service.calendarList().list().execute()
        calendars_list = res.get('items', None)
        assert calendars_list

        matched = filter(
            lambda cal_dict: cal_dict.get("summary", None) == cal_summary,
            calendars_list)
        if len(matched):
            return matched[0]['id']
        else:
            return None
        
    def get_reminders(self):
        super(GCalSide, self).get_reminders()


        # Get the ID of the "Reminders" calendar
        res = self.service.calendarList().list().execute()
        calendars_list = res.get('items', None)
        assert calendars_list

        tw_cal_id = filter(
            lambda cal_dict:
            cal_dict.get("summary", None) == self.props["tw_cal_summary"],
            calendars_list)[0]['id'] # The ID field should always be there.

        print("tw_cal_id: {}".format(tw_cal_id))


        events = None # TW reminder events to be filled
        request = self.service.events().list(calendarId=tw_cal_id)
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


    def update_reminder(self, rem):
        super(GCalSide, self).get_reminders()
        raise NotImplementedError("TODO")


    def _add_reminder(self, rem):
        super(GCalSide, self).get_reminders()
        raise NotImplementedError("TODO")

    def gain_access(self):
        credentials = self._get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)
