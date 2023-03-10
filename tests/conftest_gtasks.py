from typing import cast

import pytest

from syncall.types import GTasksItem

# API Reference: https://googleapis.github.io/google-api-python-client/docs/dyn/tasks_v1.html


@pytest.fixture()
def gtask(request: pytest.FixtureRequest) -> GTasksItem:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return cast(GTasksItem, request.getfixturevalue(param))


@pytest.fixture()
def gtasks_simple_done_item():
    return {
        "id": "Yl9GSzNDVWluTk9heE1sUQ",
        "kind": "tasks#task",
        "status": "completed",
        "etag": '"LTc5ODEwNzk2Mg"',
        "title": "Simple completed item",
        "updated": "2021-12-04T15:07:00.000Z",
        "selfLink": "https://www.googleapis.com/tasks/v1/lists/YUFLWXdFQ3NLczVKalZsWg/tasks/Yl9GSzNDVWluTk9heE1sUQ",
        "position": "00000000000000000001",
        "notes": """
            * Annotation: Testing adding annotation in Google Tasks\n

            * status: done\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        """,
        "due": "2021-12-04T18:07:00.000Z",
        "completed": "2021-12-04T15:07:00.000Z",
        "links": [],
    }


@pytest.fixture()
def gtasks_simple_pending_item():
    return {
        "id": "yl9gszndvwlutk9hee1suq",
        "kind": "tasks#task",
        "status": "needsAction",
        "etag": '"ltc5odewnzk2mg"',
        "title": "Simple pending item",
        "updated": "2021-12-04T15:07:00.000Z",
        "selflink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg/tasks/yl9gszndvwlutk9hee1suq",
        "position": "00000000000000000001",
        "notes": """
            * annotation: testing adding annotation in google tasks\n

            * status: pending\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        """,
        "due": "2021-12-04t18:07:00.000z",
        "links": [],
    }


@pytest.fixture()
def gtasks_deleted_pending_item():
    return {
        "id": "yl9gszndvwlutk9hee1suq",
        "deleted": True,
        "kind": "tasks#task",
        "status": "needsAction",
        "etag": '"ltc5odewnzk2mg"',
        "title": "test creating a task in google tasks",
        "updated": "2021-12-04T15:07:00.000Z",
        "selflink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg/tasks/yl9gszndvwlutk9hee1suq",
        "position": "00000000000000000001",
        "notes": """
            * annotation: testing adding annotation in google tasks\n

            * status: pending\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        """,
        "due": "2021-12-04T18:07:00.000Z",
        "links": [],
    }


@pytest.fixture()
def gtasks_completed_hidden_item():
    return {
        "id": "yl9gszndvwlutk9hee1suq",
        "deleted": False,
        "hidden": True,
        "kind": "tasks#task",
        "status": "completed",
        "etag": '"ltc5odewnzk2mg"',
        "title": "Hidden item",
        "updated": "2021-12-04T15:07:00.000Z",
        "selflink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg/tasks/yl9gszndvwlutk9hee1suq",
        "position": "00000000000000000001",
        "notes": """
            * annotation: testing adding annotation in google tasks\n

            * status: done\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        """,
        "due": "2021-12-04T18:07:00.000Z",
        "links": [],
    }


@pytest.fixture()
def gtasks_deleted_completed_item():
    return {
        "id": "yl9gszndvwlutk9hee1suq",
        "deleted": True,
        "status": "completed",
        "kind": "tasks#task",
        "etag": '"ltc5odewnzk2mg"',
        "title": "test creating a task in google tasks",
        "updated": "2021-12-04t15:07:00.000z",
        "selflink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg/tasks/yl9gszndvwlutk9hee1suq",
        "position": "00000000000000000001",
        "notes": """
            * annotation: testing adding annotation in google tasks\n

            * status: completed\n
            * uuid: 542f5dbc-b1b7-4a85-b55e-10f5f1d31847
        """,
        "due": "2021-12-04T18:07:00.000Z",
        "links": [],
    }


@pytest.fixture()
def gtasks_note_empty():
    return {
        "id": "yl9gszndvwlutk9hee1suq",
        "kind": "tasks#task",
        "status": "needsAction",
        "etag": '"ltc5odewnzk2mg"',
        "title": "test creating a task in google tasks",
        "updated": "2021-12-04T15:07:00.000Z",
        "selflink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg/tasks/yl9gszndvwlutk9hee1suq",
        "position": "00000000000000000001",
        "due": "2021-12-04T18:07:00.000Z",
        "links": [],
    }


@pytest.fixture()
def gtasks_list0():
    return {
        "etag": '"ltc5odewnzk2mg"',
        "id": "yl9gszndvwlutk9hee1suq",
        "kind": "tasks#taskList",
        "selfLink": "https://www.googleapis.com/tasks/v1/lists/yuflwxdfq3nlczvkalzswg",
        "title": "Taskwarrior Reminders",
        "updated": "2021-12-04T15:07:00.000Z",
    }
