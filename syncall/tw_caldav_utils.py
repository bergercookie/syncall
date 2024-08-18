from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Literal
from uuid import UUID

if TYPE_CHECKING:
    from item_synchronizer.types import Item

from syncall.caldav.caldav_utils import parse_caldav_item_desc

CALDAV_TASK_CANCELLED_UDA = "syncall_caldav_task_cancelled"
SYNCALL_TW_WAITING = "x-syncall-tw-waiting"
SYNCALL_TW_UUID = "x-syncall-tw-uuid"


aliases_tw_caldav_priority = {
    "l": 9,
    "m": 5,
    "h": 1,
}

aliases_caldav_tw_priority = {v: k for k, v in aliases_tw_caldav_priority.items()}


def _determine_caldav_status(tw_item: Item) -> tuple[str, Literal["true", "false"] | None]:
    tw_status = tw_item["status"]
    if tw_status == "pending":
        caldav_status = "needs-action"
        tw_waiting_ical_val = "false"
    elif tw_status == "waiting":
        caldav_status = "needs-action"
        tw_waiting_ical_val = "true"

    elif tw_status == "completed":
        if tw_item.get(CALDAV_TASK_CANCELLED_UDA, "false") == "true":
            caldav_status = "cancelled"
        else:
            caldav_status = "completed"
        tw_waiting_ical_val = None
    elif tw_status == "deleted":
        caldav_status = ""  # shouldn't matter
        tw_waiting_ical_val = None
    else:
        raise ValueError(f"Unknown status: {tw_status}")

    return caldav_status, tw_waiting_ical_val


def _determine_tw_status(caldav_item: Item) -> tuple[str, Literal["true", "false"] | None]:
    caldav_status = caldav_item["status"]
    if caldav_status in ("needs-action", "in-process"):
        if caldav_item.get(SYNCALL_TW_WAITING, "false") == "true":
            tw_status = "waiting"
        else:
            tw_status = "pending"
        task_cancelled_uda_val = None
    elif caldav_status == "completed":
        tw_status = "completed"
        task_cancelled_uda_val = "false"
    elif caldav_status == "cancelled":
        tw_status = "completed"
        task_cancelled_uda_val = "true"
    else:
        raise ValueError(f"Unknown caldav status: {caldav_status}")

    return tw_status, task_cancelled_uda_val


def convert_tw_to_caldav(tw_item: Item) -> Item:
    assert all(
        i in tw_item for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    caldav_item: Item = {}

    caldav_item["summary"] = tw_item["description"]
    # description
    caldav_item["description"] = ""
    if "annotations" in tw_item.keys():
        caldav_item["description"] = "\n".join(tw_item["annotations"])

    # uuid
    caldav_item[SYNCALL_TW_UUID] = tw_item["uuid"]

    # Status
    caldav_item["status"], caldav_item[SYNCALL_TW_WAITING] = _determine_caldav_status(
        tw_item=tw_item,
    )

    # Priority
    if "priority" in tw_item:
        caldav_item["priority"] = aliases_tw_caldav_priority[tw_item["priority"].lower()]
    else:
        caldav_item["priority"] = ""

    # Timestamps
    if "entry" in tw_item:
        caldav_item["created"] = tw_item["entry"]
    if "end" in tw_item:
        caldav_item["completed"] = tw_item["end"]
    if "modified" in tw_item:
        caldav_item["last-modified"] = tw_item["modified"]

    # Start/due dates
    # - If given due date -> (start=due-1, end=due)
    if "due" in tw_item:
        caldav_item["start"] = tw_item["due"] - timedelta(hours=1)
        caldav_item["due"] = tw_item["due"]

    if "tags" in tw_item:
        caldav_item["categories"] = tw_item["tags"]

    # if start-ed, override the status appropriately
    if "start" in tw_item:
        caldav_item["status"] = "in-process"

    return caldav_item


def convert_caldav_to_tw(caldav_item: Item) -> Item:
    # Parse the description by old format
    annotations, uuid = parse_caldav_item_desc(caldav_item)
    assert isinstance(annotations, list)
    assert isinstance(uuid, UUID) or uuid is None

    # tasks created directly from thunderbird do not contains a status (Marked as "Not
    # Specified" in Thunderbird). Assume they're pending
    if not caldav_item["status"]:
        caldav_item["status"] = "needs-action"

    tw_item: Item = {}

    tw_item["description"] = caldav_item.get("summary")
    tw_item["annotations"] = annotations
    if uuid is not None:  # old format
        tw_item["uuid"] = uuid
    else:  # uuid not found, try new format
        if "description" in caldav_item.keys():
            tw_item["annotations"] = [
                line.strip() for line in caldav_item["description"].split("\n") if line
            ]
        if SYNCALL_TW_UUID in caldav_item.keys():
            tw_item["uuid"] = UUID(caldav_item[SYNCALL_TW_UUID])

    # Status + task cancelled UDA
    tw_item["status"], tw_item[CALDAV_TASK_CANCELLED_UDA] = _determine_tw_status(
        caldav_item=caldav_item,
    )

    # Priority
    if prio := aliases_caldav_tw_priority.get(caldav_item["priority"]):
        tw_item["priority"] = prio

    # start time
    if caldav_item["status"] == "in-process" and "last-modified" in caldav_item:
        tw_item["start"] = caldav_item["last-modified"]

    # Rest of properties
    for caldav_key, tw_key in (
        ("created", "entry"),
        ("completed", "end"),
        ("last-modified", "modified"),
        ("due", "due"),
        ("categories", "tags"),
    ):
        if caldav_key in caldav_item:
            tw_item[tw_key] = caldav_item[caldav_key]

    return tw_item
