from copy import deepcopy
from typing import cast, no_type_check

import pytest

from syncall.types import NotionPageContents, NotionTodoBlockItem


@pytest.fixture()
def notion_todo(request: pytest.FixtureRequest) -> NotionTodoBlockItem:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return cast(NotionTodoBlockItem, request.getfixturevalue(param))


@pytest.fixture()
def notion_simple_todo() -> NotionTodoBlockItem:
    """Simple to_do block returned by Notion Python SDK.

    - Unarchived (not deleted)
    - Unchecked (not completed)
    """
    return {
        "object": "block",
        "id": "7de89eb6-4ee1-472c-abcd-8231049e9d8d",
        "created_time": "2021-11-04T19:07:00.000Z",
        "last_edited_time": "2021-12-04T10:01:00.000Z",
        "has_children": False,
        "archived": False,
        "type": "to_do",
        "to_do": {
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
            "checked": False,
        },
    }


@pytest.fixture()
def notion_simple_checked_todo(notion_simple_todo: NotionTodoBlockItem) -> NotionTodoBlockItem:
    """Completed Notion todo block."""
    item = deepcopy(notion_simple_todo)
    item["to_do"]["checked"] = True
    return item


@pytest.fixture()
def notion_simple_diff_edited_time_todo(
    notion_simple_todo: NotionTodoBlockItem,
) -> NotionTodoBlockItem:
    """Completed Notion todo block."""
    item = deepcopy(notion_simple_todo)
    item["last_edited_time"] = "2022-01-04T10:01:00.000Z"
    return item


@pytest.fixture()
def notion_simple_archived_todo(
    notion_simple_todo: NotionTodoBlockItem,
) -> NotionTodoBlockItem:
    """Archived Notion todo block."""
    item = deepcopy(notion_simple_todo)
    item["archived"] = True
    return item


@pytest.fixture()
def notion_chained_todo() -> NotionTodoBlockItem:
    """
    More complex to_do block returned by Notion Python SDK.

    Represents a todo with the following text (markdown notation in use):

        "Bringing it *back* with *style* and *glamour*"
    """
    return {
        "object": "block",
        "id": "9146e728-d7c4-4678-bab4-377a3991ebb8",
        "created_time": "2021-11-04T19:07:00.000Z",
        "last_edited_time": "2021-12-04T11:30:00.000Z",
        "has_children": False,
        "archived": False,
        "type": "to_do",
        "to_do": {
            "text": [
                {
                    "type": "text",
                    "text": {"content": "Bringing it ", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "plain_text": "Bringing it ",
                    "href": None,
                },
                {
                    "type": "text",
                    "text": {"content": "back", "link": None},
                    "annotations": {
                        "bold": True,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "plain_text": "back",
                    "href": None,
                },
                {
                    "type": "text",
                    "text": {"content": " with ", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "plain_text": " with ",
                    "href": None,
                },
                {
                    "type": "text",
                    "text": {"content": "style", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": True,
                        "color": "default",
                    },
                    "plain_text": "style",
                    "href": None,
                },
                {
                    "type": "text",
                    "text": {"content": " and ", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": False,
                        "color": "default",
                    },
                    "plain_text": " and ",
                    "href": None,
                },
                {
                    "type": "text",
                    "text": {"content": "glamour", "link": None},
                    "annotations": {
                        "bold": False,
                        "italic": False,
                        "strikethrough": False,
                        "underline": False,
                        "code": True,
                        "color": "default",
                    },
                    "plain_text": "glamour",
                    "href": None,
                },
            ],
            "checked": False,
        },
    }


@no_type_check
@pytest.fixture()
def page_contents() -> NotionPageContents:
    """
    Full example contents of a notion page.

    Fetched using the query: "notion.blocks.children.list(block_id=page_id)"
    """
    return {
        "object": "list",
        "results": [
            {
                "object": "block",
                "id": "6d64d372-fdc5-4063-8702-7dac91b52d69",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-06T09:39:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "👋 Welcome to Notion!", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "👋 Welcome to Notion!",
                            "href": None,
                        }
                    ]
                },
            },
            {
                "object": "block",
                "id": "3222c4e1-6e31-480c-9643-801481c28804",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "Here are the basics:", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Here are the basics:",
                            "href": None,
                        }
                    ]
                },
            },
            {
                "object": "block",
                "id": "7de89eb6-4ee1-472c-abcd-8231049e9d8d",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-12-04T15:08:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "to_do",
                "to_do": {
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
                },
            },
            {
                "object": "block",
                "id": "9146e728-d7c4-4678-bab4-377a3991ebb8",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-12-04T11:30:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "to_do",
                "to_do": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "Bringing it ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Bringing it ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "back", "link": None},
                            "annotations": {
                                "bold": True,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "back",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " with ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " with ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "style", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "style",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " and ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " and ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "glamour", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "glamour",
                            "href": None,
                        },
                    ],
                    "checked": False,
                },
            },
            {
                "object": "block",
                "id": "2c138594-7d72-4722-95eb-c674a9b896bc",
                "created_time": "2021-12-05T10:40:00.000Z",
                "last_edited_time": "2021-12-05T10:40:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "a list item", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "a list item",
                            "href": None,
                        }
                    ]
                },
            },
            {
                "object": "block",
                "id": "65549263-e79c-4171-9eac-150270b4d08c",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-12-04T11:30:00.000Z",
                "has_children": True,
                "archived": False,
                "type": "to_do",
                "to_do": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    "Highlight any text, and use the menu that pops up to "
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                "Highlight any text, and use the menu that pops up to "
                            ),
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "style", "link": None},
                            "annotations": {
                                "bold": True,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "style",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "your", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": True,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "your",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "writing", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": True,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "writing",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "however", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "however",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": " ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "you",
                                "link": {"url": "https://www.notion.so/product"},
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "you",
                            "href": "https://www.notion.so/product",
                        },
                        {
                            "type": "text",
                            "text": {"content": " ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "like", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "yellow_background",
                            },
                            "plain_text": "like",
                            "href": None,
                        },
                    ],
                    "checked": False,
                },
            },
            {
                "object": "block",
                "id": "879dca60-6547-4666-83b9-4e3757feb764",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "to_do",
                "to_do": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "See the ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "See the ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "⋮⋮", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "⋮⋮",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    " to the left of this checkbox on hover? Click and drag to"
                                    " move this line"
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                " to the left of this checkbox on hover? Click and drag to"
                                " move this line"
                            ),
                            "href": None,
                        },
                    ],
                    "checked": False,
                },
            },
            {
                "object": "block",
                "id": "abe925e4-17fe-46bc-99ea-61514539ee2e",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "to_do",
                "to_do": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "Click the ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Click the ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "+ New Page", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "+ New Page",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    " button at the bottom of your sidebar to add a new page"
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                " button at the bottom of your sidebar to add a new page"
                            ),
                            "href": None,
                        },
                    ],
                    "checked": False,
                },
            },
            {
                "object": "block",
                "id": "493b0be5-1fd0-4177-9485-37b62899143c",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "to_do",
                "to_do": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "Click ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Click ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "Templates", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "Templates",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    " in your sidebar to get started with pre-built pages"
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                " in your sidebar to get started with pre-built pages"
                            ),
                            "href": None,
                        },
                    ],
                    "checked": False,
                },
            },
            {
                "object": "block",
                "id": "b2603f4e-613a-4d4d-b101-cb25ea4f1690",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": True,
                "archived": False,
                "type": "toggle",
                "toggle": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    "This is a toggle block. Click the little triangle to see"
                                    " more useful tips!"
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                "This is a toggle block. Click the little triangle to see more"
                                " useful tips!"
                            ),
                            "href": None,
                        }
                    ]
                },
            },
            {
                "object": "block",
                "id": "527fc9d0-03ed-40a7-9697-5c922d65fb56",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
            {
                "object": "block",
                "id": "2e86ff5c-2c51-47ab-9a0e-a88ef476e05b",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "See it in action:", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "See it in action:",
                            "href": None,
                        }
                    ]
                },
            },
            {
                "object": "block",
                "id": "463391b6-4187-4d17-91a9-7bcf70f72fa8",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "video",
                "video": {
                    "caption": [
                        {
                            "type": "text",
                            "text": {"content": "1 minute", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "1 minute",
                            "href": None,
                        }
                    ],
                    "type": "external",
                    "external": {"url": "https://youtu.be/TL_N2pmh9O0"},
                },
            },
            {
                "object": "block",
                "id": "6e9448d5-20b0-4436-811d-8ef8ad1824c3",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
            {
                "object": "block",
                "id": "85f3e6bc-b107-4145-937c-a2e360b4bde0",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "video",
                "video": {
                    "caption": [
                        {
                            "type": "text",
                            "text": {"content": "4 minutes", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "4 minutes",
                            "href": None,
                        }
                    ],
                    "type": "external",
                    "external": {"url": "https://youtu.be/FXIrojSK3Jo"},
                },
            },
            {
                "object": "block",
                "id": "ccae9af0-9958-43e2-b0af-38a6b62ee578",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
            {
                "object": "block",
                "id": "d01b32da-cae3-4e48-8f93-e9dd4ab8e29f",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "video",
                "video": {
                    "caption": [
                        {
                            "type": "text",
                            "text": {"content": "2 minutes", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "2 minutes",
                            "href": None,
                        }
                    ],
                    "type": "external",
                    "external": {"url": "https://youtu.be/2Pwzff-uffU"},
                },
            },
            {
                "object": "block",
                "id": "52e94fb2-26a1-4103-8141-bbe62d6f7e08",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
            {
                "object": "block",
                "id": "9eb1c96f-d9f6-4124-9bef-9324e4b81cbe",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "video",
                "video": {
                    "caption": [
                        {
                            "type": "text",
                            "text": {"content": "2 minutes", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "2 minutes",
                            "href": None,
                        }
                    ],
                    "type": "external",
                    "external": {"url": "https://youtu.be/O8qdvSxDYNY"},
                },
            },
            {
                "object": "block",
                "id": "c95d7041-167c-4e56-9f99-e702f7b16249",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "Visit our ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Visit our ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": "YouTube channel",
                                "link": {"url": "http://youtube.com/c/notion"},
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "red",
                            },
                            "plain_text": "YouTube channel",
                            "href": "http://youtube.com/c/notion",
                        },
                        {
                            "type": "text",
                            "text": {"content": " to watch 50+ more tutorials", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": " to watch 50+ more tutorials",
                            "href": None,
                        },
                    ]
                },
            },
            {
                "object": "block",
                "id": "3176ca05-7c5e-4ae4-8645-fef49b5326a4",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
            {
                "object": "block",
                "id": "f1d7ddc1-6bff-49ce-801d-b474082fa406",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {"content": "👉", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "👉",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "Have a question? ", "link": None},
                            "annotations": {
                                "bold": True,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Have a question? ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "Click the ", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Click the ",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {"content": "?", "link": None},
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": True,
                                "color": "default",
                            },
                            "plain_text": "?",
                            "href": None,
                        },
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    " at the bottom right for more guides, or to send us a"
                                    " message."
                                ),
                                "link": None,
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": (
                                " at the bottom right for more guides, or to send us a"
                                " message."
                            ),
                            "href": None,
                        },
                    ]
                },
            },
            {
                "object": "block",
                "id": "1134d351-1baf-4731-9c50-a8d418f4c3d0",
                "created_time": "2021-11-04T19:07:00.000Z",
                "last_edited_time": "2021-11-04T19:07:00.000Z",
                "has_children": False,
                "archived": False,
                "type": "paragraph",
                "paragraph": {"text": []},
            },
        ],
        "next_cursor": None,
        "has_more": False,
    }  # type: ignore
