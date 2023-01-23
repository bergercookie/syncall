import pickle
from pathlib import Path
from typing import Sequence

from bubop import logger
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from syncall.sync_side import SyncSide


class GoogleSide(SyncSide):
    """Abstract parent for integrations that consume Google services."""

    def __init__(
        self,
        scopes: Sequence[str],
        oauth_port: int,
        credentials_cache: Path,
        client_secret: Path,
        **kargs,
    ):
        super().__init__(**kargs)

        self._scopes = scopes
        self._oauth_port = oauth_port
        self._client_secret = client_secret
        self._credentials_cache = credentials_cache

        # If you modify this, delete your previously saved credentials
        self._service = None

    def _get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        :return: Credentials, the obtained credentials.
        """

        creds = None
        credentials_cache = self._credentials_cache
        if credentials_cache.is_file():
            with credentials_cache.open("rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            logger.debug("Invalid credentials. Fetching again...")
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secret = self._client_secret
                flow = InstalledAppFlow.from_client_secrets_file(client_secret, self._scopes)
                try:
                    creds = flow.run_local_server(port=self._oauth_port)
                except OSError as e:
                    raise RuntimeError(
                        f"Port {self._oauth_port} is already in use, please specify a"
                        " different port or stop the process that's already using it."
                    ) from e

            # Save the credentials for the next run
            with credentials_cache.open("wb") as f:
                pickle.dump(creds, f)
        else:
            logger.info("Using already cached credentials...")

        return creds
