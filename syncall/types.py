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


# Task as returned from taskw.get_task(id=...)
TwRawItem = Tuple[Optional[int], Dict[str, Any]]
TwItem = Dict[str, Any]
