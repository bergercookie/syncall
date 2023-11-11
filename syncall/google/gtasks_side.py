import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union, cast

import dateutil
import pkg_resources
import pytz
from bubop import format_datetime_tz, logger
from googleapiclient import discovery
from googleapiclient.http import HttpError

from syncall.google.google_side import GoogleSide
from syncall.sync_side import SyncSide
from syncall.types import GTasksItem, GTasksList

DEFAULT_CLIENT_SECRET = pkg_resources.resource_filename(
    "syncall", os.path.join("res", "gtasks_client_secret.json")
)

# API Reference: https://googleapis.github.io/google-api-python-client/docs/dyn/tasks_v1.html

# NOTE(kisseliov): type hints supplied by google client library are
# questionable, this is why you might see some # type: ignore comments


class GTasksSide(GoogleSide):
    """GTasksSide interacts with the Google Tasks API.


    Adds, removes, and updates events on Google Tasks. Also handles the
    OAuth2 user authentication workflow.
    """

    ID_KEY = "id"
    TITLE_KEY = "title"
    LAST_MODIFICATION_KEY = "updated"
    _date_keys = ["updated"]

    # don't put the "due" key for comparison
    # due key holds the date but not the time that the use has set from the UI so we cannot
    # really use it for bi-synchronization.
    #
    # https://stackoverflow.com/questions/65956873/google-task-api-due-field
    _identical_comparison_keys = ["title", "notes", "status", *_date_keys]

    def __init__(
        self,
        *,
        task_list_title="TaskWarrior Reminders",
        client_secret,
        **kargs,
    ):
        if client_secret is None:
            client_secret = DEFAULT_CLIENT_SECRET

        super().__init__(
            name="Gtasks",
            fullname="Google Tasks",
            scopes=["https://www.googleapis.com/auth/tasks"],
            credentials_cache=Path.home() / ".gtasks_credentials.pickle",
            client_secret=client_secret,  # type: ignore
            **kargs,
        )

        self._task_list_title = task_list_title
        self._task_list_id: Optional[str] = None
        self._items_cache: Dict[str, dict] = {}

    def start(self):
        logger.debug("Connecting to Google Tasks...")
        creds = self._get_credentials()
        self._service = discovery.build("tasks", "v1", credentials=creds)
        self._task_list_id = self._fetch_task_list_id()

        # Create task list if not there --------------------------------------------------------
        if self._task_list_id is None:
            logger.info(f"Creating task list {self._task_list_title}")
            new_task_list = {"title": self._task_list_title}
            ret = self._service.tasklists().insert(body=new_task_list).execute()  # type: ignore
            assert "id" in ret
            new_task_list_id = ret["id"]
            logger.info(f"Created task list, id: {new_task_list_id}")
            self._task_list_id = new_task_list_id

        logger.debug("Connected to Google Tasks.")

    def _fetch_task_list_id(self) -> Optional[str]:
        """Return the id of the task list based on the given Title.

        :returns: id or None if that was not found
        """
        res = self._service.tasklists().list().execute()  # type: ignore
        task_lists_list: List[GTasksList] = res["items"]  # type: ignore

        matching_task_lists = [
            list["id"] for list in task_lists_list if list["title"] == self._task_list_title
        ]

        if len(matching_task_lists) == 0:
            return None
        elif len(matching_task_lists) == 1:
            return cast(str, matching_task_lists[0])
        else:
            raise RuntimeError(
                f'Multiple matching task lists for title -> "{self._task_list_title}"'
            )

    def _clear_all_task_list_entries(self):
        """Clear all tasks from the current task list."""
        logger.warning(f"Clearing all tasks from task list {self._task_list_id}")
        self._service.tasks().clear(tasklist=self._task_list_id).execute()  # type

    def get_all_items(self, **kargs) -> Sequence[GTasksItem]:
        """Get all tasks for the task list that we use.

        :param kargs: Extra options for the call
        """
        # Get the ID of the task list of interest
        tasks = []

        if self._task_list_id is not None:
            request = self._service.tasks().list(
                tasklist=self._task_list_id,
                # TL;DR Set showCompleted=True AND showHidden=True if you want to also get the
                # items that the user has ticked from the app.
                #
                # From the ref: https://developers.google.com/tasks/reference/rest/v1/tasks/list
                #
                # Flag indicating whether completed tasks are returned in the result. Optional.
                # The default is True. Note that showHidden must also be True to show tasks
                # completed in first party clients, such as the web UI and Google's mobile
                # apps.
                showCompleted=True,
                showDeleted=False,
                showHidden=True,
            )  # type: ignore
        else:
            raise RuntimeError("You have to provide valid task list ID")

        # Loop until all pages have been processed.
        while request is not None:
            # Get the next page.
            response = request.execute()

            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (tasks).
            tasks.extend(
                [
                    t
                    for t in response.get("items", [])
                    if t["status"] != "deleted" and len(t["title"]) > 0
                ]
            )

            # Get the next request object by passing the previous request
            # object to the list_next method.
            request = self._service.tasks().list_next(request, response)  # type: ignore

        # cache them
        for t in tasks:
            self._items_cache[t["id"]] = t

        return tasks

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[dict]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            item = self._get_item_refresh(item_id=item_id)

        return item

    def _get_item_refresh(self, item_id: str) -> Optional[dict]:
        ret = None
        try:
            ret = (
                self._service.tasks().get(tasklist=self._task_list_id, task=item_id).execute()
            )
            if ret["status"] == "deleted":
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
        task = self._service.tasks().get(tasklist=self._task_list_id, task=item_id).execute()  # type: ignore
        task.update(changes)
        self._service.tasks().update(  # type: ignore
            tasklist=self._task_list_id, task=task["id"], body=task
        ).execute()

    def add_item(self, item) -> dict:
        task = self._service.tasks().insert(tasklist=self._task_list_id, body=item).execute()  # type: ignore
        logger.debug(f'Task created -> {task.get("selfLink")}')

        return task

    def delete_single_item(self, item_id) -> None:
        self._service.tasks().delete(tasklist=self._task_list_id, task=item_id).execute()  # type: ignore

    @classmethod
    def id_key(cls) -> str:
        return cls.ID_KEY

    @classmethod
    def summary_key(cls) -> str:
        return cls.TITLE_KEY

    @classmethod
    def last_modification_key(cls) -> str:
        return cls.LAST_MODIFICATION_KEY

    @staticmethod
    def _parse_dt_or_none(item: GTasksItem, field: str) -> Optional[datetime.datetime]:
        """Return the datetime on which task was completed in datetime format."""
        if (dt := item.get(field)) is not None:
            dt_dt = GTasksSide.parse_datetime(dt)
            assert isinstance(dt_dt, datetime.datetime)
            return dt_dt
        else:
            return None

    @staticmethod
    def get_task_due_time(item: GTasksItem) -> Optional[datetime.datetime]:
        """Return the datetime on which task is due in datetime format."""
        return GTasksSide._parse_dt_or_none(item=item, field="due")

    @staticmethod
    def get_task_completed_time(item: GTasksItem) -> Optional[datetime.datetime]:
        """Return the datetime on which task was completed in datetime format."""
        return GTasksSide._parse_dt_or_none(item=item, field="completed")

    @staticmethod
    def format_datetime(dt: datetime.datetime) -> str:
        assert isinstance(dt, datetime.datetime)
        return format_datetime_tz(dt)

    @classmethod
    def parse_datetime(cls, dt: Union[str, dict, datetime.datetime]) -> datetime.datetime:
        """
        Parse datetime given in the GTasks format(s):
        - string with ('T', 'Z' separators).
        - (dateTime, dateZone) dictionary
        - datetime object

        Usage::

        >>> GTasksSide.parse_datetime("2019-03-05T00:03:09Z")
        datetime.datetime(2019, 3, 5, 0, 3, 9)
        >>> GTasksSide.parse_datetime("2019-03-05")
        datetime.datetime(2019, 3, 5, 0, 0)
        >>> GTasksSide.parse_datetime("2019-03-05T00:03:01.1234Z")
        datetime.datetime(2019, 3, 5, 0, 3, 1, 123400)
        >>> GTasksSide.parse_datetime("2019-03-08T00:29:06.602Z")
        datetime.datetime(2019, 3, 8, 0, 29, 6, 602000)

        >>> from tzlocal import get_localzone_name
        >>> tz = get_localzone_name()
        >>> a = GTasksSide.parse_datetime({"dateTime": "2021-11-14T22:07:49Z", "timeZone": tz})
        >>> b = GTasksSide.parse_datetime({"dateTime": "2021-11-14T22:07:49.000000Z"})
        >>> b
        datetime.datetime(2021, 11, 14, 22, 7, 49)
        >>> from bubop.time import is_same_datetime
        >>> is_same_datetime(a, b) or (print(a) or print(b))
        True
        >>> GTasksSide.parse_datetime({"dateTime": "2021-11-14T22:07:49.123456"})
        datetime.datetime(2021, 11, 14, 22, 7, 49, 123456)
        >>> a = GTasksSide.parse_datetime({"dateTime": "2021-11-14T22:07:49Z", "timeZone": tz})
        >>> GTasksSide.parse_datetime(a).isoformat() == a.isoformat()
        True
        """

        if isinstance(dt, str):
            return dateutil.parser.parse(dt).replace(tzinfo=None)  # type: ignore
        elif isinstance(dt, dict):
            date_time = dt.get("dateTime")
            if date_time is None:
                raise RuntimeError(f"Invalid structure dict: {dt}")
            dt_dt = GTasksSide.parse_datetime(date_time)
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
