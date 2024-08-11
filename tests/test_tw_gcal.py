import datetime
from typing import Mapping

import pytest
from dateutil.tz import tzutc
from syncall.tw_gcal_utils import convert_gcal_to_tw, convert_tw_to_gcal
from syncall.types import GCalItem, TwItem


# Expected properties when converting GCal -> TW ----------------------------------------------
@pytest.fixture()
def gcal_event_expected_tw_props(request):
    param = request.param
    return request.getfixturevalue(param)


@pytest.fixture()
def gcal_event_pending_expected_tw_props() -> Mapping:
    return {
        "status": "pending",
        "description": "kalimera",
        "due": datetime.datetime(2023, 2, 19, 19, 55, tzinfo=tzutc()),
    }


@pytest.fixture()
def gcal_event_completed_expected_tw_props() -> Mapping:
    return {
        "status": "completed",
        "description": "hey there",
        "due": datetime.datetime(2023, 2, 18, 22, 0, tzinfo=tzutc()),
    }


@pytest.mark.parametrize(
    ("gcal_event", "gcal_event_expected_tw_props"),
    [
        ("gcal_event_pending", "gcal_event_pending_expected_tw_props"),
        ("gcal_event_completed", "gcal_event_completed_expected_tw_props"),
    ],
    indirect=True,
)
def test_convert_gcal_to_tw(gcal_event: GCalItem, gcal_event_expected_tw_props):
    tw_task = convert_gcal_to_tw(gcal_event)
    for key, expected_value in gcal_event_expected_tw_props.items():
        assert expected_value == tw_task[key]


# Expected properties when converting TW -> GCal ----------------------------------------------
@pytest.fixture()
def tw_item_expected_gcal_props(request):
    param = request.param
    return request.getfixturevalue(param)


@pytest.fixture()
def tw_pending_task_expected_gcal_props() -> Mapping:
    return {
        "summary": "Arrange to do any home pre-departure covid tests",
        "description": lambda gcal_item: all(
            match in gcal_item["description"]
            for match in ("status: pending", "b2645524-6a3d-4fa2-b8c5-3bf155d03506")
        ),
        "start": {"dateTime": "2023-03-10T11:26:07.000000Z"},
    }


@pytest.fixture()
def tw_pending_with_due_task_expected_gcal_props() -> Mapping:
    return {
        "summary": "Create and share public photos album",
        "description": lambda gcal_item: all(
            match in gcal_item["description"]
            for match in ("status: pending", "14bcfc87-a4fe-4c32-898b-179b154a03d1")
        ),
        "start": {"dateTime": "2023-03-12T21:00:00.000000Z"},
        "end": {"dateTime": "2023-03-12T22:00:00.000000Z"},
    }


@pytest.fixture()
def tw_completed_task_expected_gcal_props() -> Mapping:
    return {
        "summary": "✅Arrange to do any home pre-departure covid tests",
        "description": lambda gcal_item: all(
            match in gcal_item["description"]
            for match in ("status: completed", "b2645524-6a3d-4fa2-b8c5-3bf155d03506")
        ),
        "start": {"dateTime": "2023-03-10T11:26:07.000000Z"},
    }


@pytest.mark.parametrize(
    ("tw_task", "tw_item_expected_gcal_props"),
    [
        ("tw_pending_task", "tw_pending_task_expected_gcal_props"),
        (
            "tw_pending_with_due_task",
            "tw_pending_with_due_task_expected_gcal_props",
        ),
        ("tw_completed_task", "tw_completed_task_expected_gcal_props"),
    ],
    indirect=True,
)
def test_convert_tw_to_gcal(tw_task: TwItem, tw_item_expected_gcal_props):
    gcal_event = convert_tw_to_gcal(tw_task)
    for key, expected_value in tw_item_expected_gcal_props.items():
        if callable(expected_value):
            assert expected_value(gcal_event)
        else:
            assert expected_value == gcal_event[key]
