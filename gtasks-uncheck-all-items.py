#!/usr/bin/env python3

"""
Login to google account, based on either the cached credentials or using interactive oAuth2
authentication via the browser. Then given the task list name, uncheck all the items in that
list.
"""

import logging
import pickle
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Optional, Sequence, cast

import pkg_resources
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


def parse_args() -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("task_list", help="Name of the list of tasks to uncheck its items")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    return parser.parse_args()


class GoogleTasksUnchecker:
    def __init__(
        self,
        scopes: Sequence[str],
        oauth_port: int,
        credentials_cache: Path,
        client_secret: str,
        logger: logging.Logger,
        **kargs,
    ):
        super().__init__(**kargs)

        self._scopes = scopes
        self._oauth_port = oauth_port
        self._client_secret = client_secret
        self._credentials_cache = credentials_cache
        self._logger = logger

        # If you modify this, delete your previously saved credentials
        self._service = None

    def fetch_and_cache_credentials(self):
        """Get valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        :return: Credentials, the obtained credentials.
        """
        creds = None
        credentials_cache = self._credentials_cache
        if credentials_cache.is_file():
            with credentials_cache.open("rb") as f:
                creds = pickle.load(f)  # noqa: S301

        if not creds or not creds.valid:
            self._logger.debug("Invalid credentials. Fetching again...")
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._client_secret,
                    self._scopes,
                )
                try:
                    creds = flow.run_local_server(port=self._oauth_port)
                except OSError as e:
                    raise RuntimeError(
                        f"Port {self._oauth_port} is already in use, please specify a"
                        " different port or stop the process that's already using it.",
                    ) from e

            # Save the credentials for the next run
            with credentials_cache.open("wb") as f:
                pickle.dump(creds, f)
        else:
            self._logger.info("Using already cached credentials...")

        return creds

    def fetch_task_list_id(self, title: str, must_exist: bool = True) -> Optional[str]:
        """Return the id of the task list based on the given Title.

        :returns: id or None if that was not found
        """
        res = self._service.tasklists().list().execute()  # type: ignore
        task_lists_list: list[GTasksList] = res["items"]  # type: ignore

        matching_task_lists = [
            task_list["id"] for task_list in task_lists_list if task_list["title"] == title
        ]

        if len(matching_task_lists) == 0:
            if must_exist:
                raise ValueError(f'Task list with title "{title}" not found')

            return None

        if len(matching_task_lists) == 1:
            return cast(str, matching_task_lists[0])

        raise RuntimeError(
            f'Multiple matching task lists for title -> "{title}"',
        )

    def uncheck_all_items(self, list_id: str):
        """Uncheck all the items in the given list."""
        self._logger.debug('Unchecking all items in the list "%s"', list_id)
        pass


def main():
    args = parse_args()

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG if args.is_verbose else logging.INFO)

    DEFAULT_CLIENT_SECRET = pkg_resources.resource_filename(
        "syncall",
        "res/gtasks_client_secret.json",
    )

    # Initialize the google side instance -----------------------------------------------------
    unchecker = GoogleTasksUnchecker(
        name="Gtasks",
        fullname="Google Tasks List Unchecker",
        scopes=["https://www.googleapis.com/auth/tasks"],
        credentials_cache=Path.home() / ".gtasks_credentials.pickle",
        client_secret=DEFAULT_CLIENT_SECRET,
        oauth_port=8081,
        logger=logger,
    )

    # connect with your credentials -----------------------------------------------------------
    logger.debug("Connecting to Google Tasks...")
    unchecker.fetch_and_cache_credentials()
    task_list_id = unchecker.fetch_task_list_id(title=args.task_list, must_exist=True)
    assert task_list_id is not None

    logger.debug("Connected to Google Tasks.")
    unchecker.uncheck_all_items(list_id=task_list_id)


if __name__ == "__main__":
    main()
