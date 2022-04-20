import pytest

from syncall.types import TwRawItem


@pytest.fixture()
def tw_task(request: pytest.FixtureRequest) -> TwRawItem:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return request.getfixturevalue(param)


@pytest.fixture()
def tw_simple_pending_task() -> TwRawItem:
    return (
        345,
        {
            "id": 345,
            "description": "Arrange to do any home pre-departure covid tests",
            "entry": "20201027T104745Z",
            "modified": "20201027T104745Z",
            "project": "travelling",
            "status": "pending",
            "uuid": "3e3fdd67-b8b7-4924-bd86-36daa2e9c1c9",
            "urgency": 1.20822,
        },
    )


@pytest.fixture()
def tw_simple_completed_task() -> TwRawItem:
    return (
        None,
        {
            "id": 0,
            "description": "Talk with family",
            "due": "20211130T173800Z",
            "end": "20211130T213004Z",
            "entry": "20211129T180001Z",
            "imask": 71,
            "modified": "20211130T213004Z",
            "parent": "d39deae3-01b7-4c31-831e-e1fbea526830",
            "recur": "daily",
            "rtype": "periodic",
            "status": "completed",
            "uuid": "48d74cbd-d2ec-40ce-915b-d17bc7842fff",
            "tags": ["remindme", "routine"],
            "urgency": 6.4936,
        },
    )
