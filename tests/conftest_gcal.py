import datetime

import pytest
from dateutil.tz import tzutc
from syncall.types import GCalItem


@pytest.fixture()
def gcal_event(request: pytest.FixtureRequest) -> GCalItem:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return request.getfixturevalue(param)


@pytest.fixture()
def gcal_event_pending() -> GCalItem:
    return {
        "kind": "calendar#event",
        "etag": '"3353664413330000"',
        "id": "3p9ssstnv1fcl7991lu99q6q3n",
        "status": "confirmed",
        "htmlLink": "https://www.google.com/calendar/event?eid=M3A5c3NzdG52MWZjbDc5OTFsdTk5cTZxM24gYTl1a2t1MXAxNzhqaG91bmR1dnRqOWdhaThAZw",
        "created": "2023-02-19T18:43:26.000Z",
        "updated": "2023-02-19T18:43:26.665Z",
        "summary": "kalimera",
        "creator": {"email": "nickkouk@gmail.com"},
        "organizer": {
            "email": "a9ukku1p178jhounduvtj9gai8@group.calendar.google.com",
            "displayName": "tw_test",
            "self": True,
        },
        "start": {"dateTime": "2023-02-19T19:15:00Z", "timeZone": "Europe/Athens"},
        "end": {"dateTime": "2023-02-19T19:55:00Z", "timeZone": "Europe/Athens"},
        "iCalUID": "3p9ssstnv1fcl7991lu99q6q3n@google.com",
        "sequence": 0,
        "reminders": {"useDefault": True},
        "eventType": "default",
    }


@pytest.fixture()
def gcal_event_completed() -> GCalItem:
    return {
        "kind": "calendar#event",
        "etag": '"3353665840950000"',
        "id": "7p4qm5po5fpltqs33bk0npos48",
        "status": "confirmed",
        "htmlLink": "https://www.google.com/calendar/event?eid=N3A0cW01cG81ZnBsdHFzMzNiazBucG9zNDggYTl1a2t1MXAxNzhqaG91bmR1dnRqOWdhaThAZw",
        "created": "2023-02-19T18:54:55.000Z",
        "updated": datetime.datetime(2023, 2, 19, 18, 55, 20, 475000, tzinfo=tzutc()),
        "summary": "hey there",
        "description": (
            "IMPORTED FROM TASKWARRIOR\n\n\n* status: completed\n* uuid:"
            " 108aab03-402e-4d34-b2a0-648228168e50"
        ),
        "creator": {"email": "nickkouk@gmail.com"},
        "organizer": {
            "email": "a9ukku1p178jhounduvtj9gai8@group.calendar.google.com",
            "displayName": "tw_test",
            "self": True,
        },
        "start": datetime.datetime(2023, 2, 18, 21, 30, tzinfo=tzutc()),
        "end": datetime.datetime(2023, 2, 18, 22, 0, tzinfo=tzutc()),
        "iCalUID": "7p4qm5po5fpltqs33bk0npos48@google.com",
        "sequence": 0,
        "reminders": {"useDefault": True},
        "eventType": "default",
    }
