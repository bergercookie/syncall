from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union

from item_synchronizer.types import ID


# ---------------------------------------------------------------------------------------------
# Taskwarrior
class TaskwarriorRawItem(TypedDict, total=False):
    """Dictionary part of an item as returned from the Taskw Python API on tw.get_task(id=...).

    Example:

        {'id': 473,
        'description': 'buenos dias',
        'entry': '20211209T083645Z',
        'modified': '20211209T190248Z',
        'project': 'travelling.sometravel',
        'status': 'pending',
        'uuid': 'a06f1c9d-237a-4692-8427-27bf6cad5ff1',
        'tags': ['test', 'test2'],
        'urgency': 1.9})
    """

    id: int
    description: str
    entry: str
    imask: int
    modified: str
    parent: str
    recur: str
    rtype: str
    project: str
    status: str
    uuid: str
    tags: List[str]
    urgency: float


# Item as returned from the Taskw Python API on tw.get_task(id=...)
TaskwarriorRawTuple = Tuple[Optional[int], TaskwarriorRawItem]

# Google Calendar -----------------------------------------------------------------------------
GCalItem = Dict[str, Any]

# ---------------------------------------------------------------------------------------------
# Google Tasks


class GTaskLink(TypedDict):
    description: str
    link: str
    type: str  # "email"


class GTasksList(TypedDict):
    etag: str  # ETag of the resource.
    id: str  # Task list identifier.
    kind: str  # Type of the resource. This is always "tasks#taskList".
    selfLink: str  # URL pointing to this task list. Used to retrieve, update, or delete this task list.
    title: str  # Title of the task list.
    updated: str  # Last modification time of the task list (as a RFC 3339 timestamp).


class GTasksItem(TypedDict):
    """
    Dict part of an item as returned from the Google Tasks Python API on `tasks().get_task()`.

    Example:

       {
        'id': 'Yl9GSzNDVWluTk9heE1sUQ',
        'kind': 'tasks#task',
        'status': 'completed',
        'etag': '"LTc5ODEwNzk2Mg"',
        'title': 'Simple completed item',
        'updated': '2021-12-04T15:07:00.000Z',
        'selfLink': 'https://www.googleapis.com/tasks/v1/lists/YUFLWXdFQ3NLczVKalZsWg/tasks/Yl9GSzNDVWluTk9heE1sUQ',
        'position': '00000000000000000001',
        'notes': '''
            * Annotation: Testing adding annotation in Google Tasks\n

            * status: done\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        ''',
        'due': '2021-12-04T18:07:00.000Z',
        "completed": "2021-12-04T15:07:00.000Z",
        'links': []
    }
    """

    # Completion date of the task (as a RFC 3339 timestamp). This field is omitted if the task
    # has not been completed.
    completed: Optional[str]
    # Flag indicating whether the task has been deleted. The default is False.
    deleted: bool
    # Due date of the task (as a RFC 3339 timestamp). Optional. The due date only records date
    # information; the time portion of the timestamp is discarded when setting the due date. It
    # isn't possible to read or write the time that a task is due via the API.
    due: Optional[str]
    # ETag of the resource.
    etag: str
    # Flag indicating whether the task is hidden. This is the case if the task had been marked
    # completed when the task list was last cleared. The default is False. This field is
    # read-only.
    hidden: bool
    # Task identifier.
    id: str
    # Type of the resource. This is always "tasks#task".
    kind: str
    # Collection of links. This collection is read-only.
    links: List[GTaskLink]
    # Notes describing the task. Optional.
    notes: Optional[str]
    # Parent task identifier. This field is omitted if it is a top-level task. This field is
    # read-only. Use the "move" method to move the task under a different parent or to the top
    # level.
    parent: Optional[str]
    # String indicating the position of the task among its sibling tasks under the same parent
    # task or at the top level. If this string is greater than another task's corresponding
    # position string according to lexicographical ordering, the task is positioned after the
    # other task under the same parent task (or at the top level). This field is read-only. Use
    # the "move" method to move the task to another position.
    position: str
    # URL pointing to this task. Used to retrieve, update, or delete this task.
    selfLink: str
    # Status of the task. This is either "needsAction" or "completed".
    status: str
    # Title of the task.
    title: str
    # Last modification time of the task (as a RFC 3339 timestamp).
    updated: str


# ---------------------------------------------------------------------------------------------
# Notion
NotionID = ID


class NotionRawItem(TypedDict):
    """Item as returned from the Notion Python API."""

    object: Literal["block"]
    # the item might not be added to Notion yet and thus not assigned an ID, created_time, etc.
    id: NotionID
    created_time: str
    last_edited_time: str
    has_children: bool
    archived: bool
    type: str


class NotionTextContent(TypedDict):
    """
    Example section:

        "text": {"content": "Lacinato kale", "link": None},
    """

    content: str
    link: Optional[str]  # ?


class SingleItemTextSection(TypedDict, total=False):
    """
    Example section:

        {
            "type": "text",
            "text": {"content": "Lacinato kale", "link": None},
            "annotations": {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            },
            "plain_text": "Lacinato kale",
            "href": None,
        }
    """

    type: Literal["text"]
    text: NotionTextContent
    annotations: Dict[str, Union[bool, str]]
    plain_text: str
    href: Optional[str]  # ?


class NotionPage(NotionRawItem):
    """
    Created page:

        {
            object: "page",
            id: "e849bbd0-6d46-42af-9809-e81628e43306",
            created_time: "2021-12-05T13:17:00.000Z",
            last_edited_time: "2021-12-05T13:17:00.000Z",
            cover: None,
            icon: None,
            parent: { type: "page_id",
                      page_id: "a6dda560-5841-4bbb-8d66-a56725c5a82a" },
            archived: False,
            properties: {
                title: {
                id: "title",
                type: "title",
                title: [
                    {
                    type: "text",
                    text: { content: "Opa, na th!", link: None },
                    annotations: {
                        bold: False,
                        italic: False,
                        strikethrough: False,
                        underline: False,
                        code: False,
                        color: "default",
                    },
                    plain_text: "Opa, na th!",
                    href: None,
                    },
                ],
                },
            },
            url: "https://www.notion.so/Opa-na-th-e849bbd06d4642af9809e81628e43306",
        }
    """

    cover: Optional[str]
    icon: Optional[str]
    parent: Dict[str, str]
    properties: Tuple[Literal["properties"], SingleItemTextSection]
    url: str


class NotionTodoSection(TypedDict):
    """
    Example section:

       {
           "text": [
               {
                   "type": "text",
                   "text": {"content": "Lacinato kale", "link": None},
                   "annotations": {
                       "bold": False,
                       "italic": False,
                       "strikethrough": False,
                       "underline": False,
                       "code": False,
                       "color": "default",
                   },
                   "plain_text": "Lacinato kale",
                   "href": None,
               }
           ],
           "checked": True,
       }
    """

    text: List[SingleItemTextSection]
    checked: bool


class NotionTodoBlockItem(NotionRawItem):
    to_do: NotionTodoSection


# Page contents as returned from the Notion Python API
class NotionPageContents(TypedDict):
    object: Literal["list"]
    results: List[NotionRawItem]
    next_cursor: Any
    has_more: bool


# ---------------------------------------------------------------------------------------------
# Asana
AsanaGID = ID


# Task as returned from Asana API.
class AsanaRawTask(TypedDict):
    completed: bool
    completed_at: str
    created_at: str
    due_at: str
    due_on: str
    gid: AsanaGID
    name: str
    modified_at: str


# Extras --------------------------------------------------------------------------------------
# Task as returned from taskw.get_task(id=...)
# TODO Are these types needed? They seem to be duplicates of TaskwarriorRawItem ...
TwRawItem = Tuple[Optional[int], Dict[str, Any]]
TwItem = Dict[str, Any]
