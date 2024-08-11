import datetime

import pytest
from dateutil.tz.tz import tzutc
from syncall.types import TwItem


@pytest.fixture()
def tw_task(request: pytest.FixtureRequest) -> TwItem:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return request.getfixturevalue(param)


@pytest.fixture()
def tw_pending_task() -> TwItem:
    return {
        "id": 686,
        "description": "Arrange to do any home pre-departure covid tests",
        "entry": datetime.datetime(2023, 3, 10, 11, 26, 7, tzinfo=tzutc()),
        "modified": datetime.datetime(2023, 3, 10, 13, 33, 48, tzinfo=tzutc()),
        "project": "a_project",
        "status": "pending",
        "uuid": "b2645524-6a3d-4fa2-b8c5-3bf155d03506",
        "urgency": 1.03836,
    }


@pytest.fixture()
def tw_pending_with_due_task() -> TwItem:
    return {
        "id": 0,
        "description": "Create and share public photos album",
        "due": datetime.datetime(2023, 3, 12, 22, 0, tzinfo=tzutc()),
        "end": datetime.datetime(2023, 3, 13, 17, 58, 12, tzinfo=tzutc()),
        "entry": datetime.datetime(2023, 1, 25, 20, 47, 26, tzinfo=tzutc()),
        "modified": datetime.datetime(2023, 3, 13, 17, 58, 12, tzinfo=tzutc()),
        "project": "travelling",
        "status": "pending",
        "uuid": "14bcfc87-a4fe-4c32-898b-179b154a03d1",
        "tags": ["remindme"],
        "urgency": 13.3259,
    }


def _as_completed(task):
    task["status"] = "completed"
    return task


@pytest.fixture()
def tw_completed_task(tw_pending_task) -> TwItem:
    return _as_completed(tw_pending_task)


@pytest.fixture()
def tw_completed_with_due_task(tw_pending_with_due_task) -> TwItem:
    return _as_completed(tw_pending_with_due_task)
