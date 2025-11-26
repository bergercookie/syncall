import datetime

import pytest
from dateutil.tz import tzutc
from syncall.caldav.caldav_side import CaldavSide
from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
from syncall.tw_caldav_utils import (
    CALDAV_TASK_CANCELLED_UDA,
    SYNCALL_TW_UUID,
    SYNCALL_TW_WAITING,
    convert_caldav_to_tw,
    convert_tw_to_caldav,
)

tw_pending_item = {
    "id": 5,
    "description": "task in project - and with date",
    "entry": datetime.datetime(2024, 8, 18, 7, 53, 40, tzinfo=tzutc()),
    "modified": datetime.datetime(2024, 8, 18, 7, 53, 40, tzinfo=tzutc()),
    "project": "kalimera",
    "status": "pending",
    "uuid": "4471f2ac-4a70-4012-9eff-b4ddfc860d26",
    "urgency": 9.74399,
}

caldav_pending_item = {
    "summary": "task in project - and with date",
    "description": "",
    "priority": 0,
    SYNCALL_TW_UUID: "4471f2ac-4a70-4012-9eff-b4ddfc860d26",
    "status": "needs-action",
    SYNCALL_TW_WAITING: "false",
    "created": datetime.datetime(2024, 8, 18, 7, 53, 40, tzinfo=tzutc()),
    "last-modified": datetime.datetime(2024, 8, 18, 7, 53, 40, tzinfo=tzutc()),
}

tw_pending_item_with_annotations = {
    **tw_pending_item,
    "annotations": ["annotation1", "annotation2"],
}

caldav_pending_item_with_annotations = {
    **caldav_pending_item,
    "description": "annotation1\nannotation2",
}

tw_waiting_item = {
    **tw_pending_item,
    "wait": datetime.datetime(2024, 8, 19, 8, 53, 40, tzinfo=tzutc()),
    "status": "waiting",
}

caldav_pending_item_waiting = {
    **caldav_pending_item,
    SYNCALL_TW_WAITING: "true",
}

tw_pending_item_with_due = {
    **tw_pending_item,
    "due": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
}

caldav_item_with_due = {
    **caldav_pending_item,
    "start": datetime.datetime(2024, 8, 18, 9, 53, 40, tzinfo=tzutc()),
    "due": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
}

tw_completed_item = {
    **tw_pending_item,
    "status": "completed",
    "end": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
}

tw_completed_item2 = {
    **tw_pending_item,
    "status": "completed",
    "end": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
    CALDAV_TASK_CANCELLED_UDA: "false",
}

caldav_completed_item_base = {
    **caldav_pending_item,
    "completed": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
    SYNCALL_TW_WAITING: None,
}

caldav_completed_item = {
    **caldav_completed_item_base,
    "status": "completed",
}

tw_completed_item_with_cancelled_uda = {
    **tw_completed_item,
    "status": "completed",
    "end": datetime.datetime(2024, 8, 18, 10, 53, 40, tzinfo=tzutc()),
    CALDAV_TASK_CANCELLED_UDA: "true",
}

caldav_cancelled_item = {
    **caldav_completed_item_base,
    "status": "cancelled",
}


def tw_pending_item_with_priority(prio: str) -> dict:
    return {
        **tw_pending_item,
        "priority": prio,
    }


def caldav_item_with_priority(prio: int) -> dict:
    return {
        **caldav_pending_item,
        "priority": prio,
    }


@pytest.mark.parametrize(
    ("tw_item", "caldav_item_expected"),
    [
        # pending_item
        (
            tw_pending_item,
            caldav_pending_item,
        ),
        # pending_item_with_annotations
        (
            tw_pending_item_with_annotations,
            caldav_pending_item_with_annotations,
        ),
        # pending_item_with_due
        (
            tw_pending_item_with_due,
            caldav_item_with_due,
        ),
        # completed_item
        (
            tw_completed_item,
            caldav_completed_item,
        ),
        # completed_item_with_cancelled_uda
        (
            tw_completed_item2,
            caldav_completed_item,
        ),
        # cancelled_item
        (
            tw_completed_item_with_cancelled_uda,
            caldav_cancelled_item,
        ),
        # pending_item_with_priority_{L,M,H}
        *(
            (
                tw_pending_item_with_priority(tw_prio),
                caldav_item_with_priority(caldav_prio),
            )
            for tw_prio, caldav_prio in [("L", 9), ("M", 5), ("H", 1)]
        ),
    ],
    ids=[
        "pending_item",
        "pending_item_with_annotations",
        "pending_item_with_due",
        "completed_item",
        "completed_item_with_cancelled_uda",
        "cancelled_item",
        "pending_item_with_priority_L",
        "pending_item_with_priority_M",
        "pending_item_with_priority_H",
    ],
)
def test_convert_tw_to_caldav_n_back(tw_item, caldav_item_expected):
    caldav_item = convert_tw_to_caldav(tw_item)
    assert CaldavSide.items_are_identical(caldav_item, caldav_item_expected)

    tw_item_reconverted = convert_caldav_to_tw(caldav_item)
    assert TaskWarriorSide.items_are_identical(tw_item_reconverted, tw_item)


@pytest.mark.parametrize(
    ("caldav_item", "tw_item_expected"),
    [
        # pending_item
        (
            caldav_pending_item,
            tw_pending_item,
        ),
        # pending_item_with_annotations
        (
            caldav_pending_item_with_annotations,
            tw_pending_item_with_annotations,
        ),
        # pending_item_with_due
        (
            caldav_item_with_due,
            tw_pending_item_with_due,
        ),
        # completed_item
        (
            caldav_completed_item,
            tw_completed_item,
        ),
        # cancelled_item
        (
            caldav_cancelled_item,
            tw_completed_item_with_cancelled_uda,
        ),
        # pending_item_with_priority_{9,5,1}
        *(
            (
                caldav_item_with_priority(caldav_prio),
                tw_pending_item_with_priority(tw_prio),
            )
            for tw_prio, caldav_prio in [("L", 9), ("M", 5), ("H", 1)]
        ),
    ],
    ids=[
        "pending_item",
        "pending_item_with_annotations",
        "pending_item_with_due",
        "completed_item",
        "cancelled_item",
        "pending_item_with_priority_9",
        "pending_item_with_priority_5",
        "pending_item_with_priority_1",
    ],
)
def test_convert_caldav_to_tw_n_back(caldav_item, tw_item_expected):
    tw_item = convert_caldav_to_tw(caldav_item)
    assert TaskWarriorSide.items_are_identical(tw_item, tw_item_expected)

    caldav_item_reconverted = convert_tw_to_caldav(tw_item)
    assert CaldavSide.items_are_identical(caldav_item_reconverted, caldav_item)
