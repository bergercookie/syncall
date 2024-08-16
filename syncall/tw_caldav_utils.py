from datetime import timedelta
from uuid import UUID

from item_synchronizer.types import Item

from syncall.caldav.caldav_utils import parse_caldav_item_desc

aliases_tw_caldav_status = {
    "completed": "completed",
    "pending": "needs-action",
    "waiting": "needs-action",
    "deleted": "cancelled",
}

aliases_caldav_tw_status = {
    "completed": "completed",
    "needs-action": "pending",
    "in-process": "pending",
    "cancelled": "deleted",
}

aliases_tw_caldav_priority = {
    "l": 9,
    "m": 5,
    "h": 1,
}

aliases_caldav_tw_priority = {v: k for k, v in aliases_tw_caldav_priority.items()}


def convert_tw_to_caldav(tw_item: Item) -> Item:
    assert all(
        i in tw_item for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    caldav_item: Item = {}

    caldav_item["summary"] = tw_item["description"]
    # description
    if "annotations" in tw_item.keys():
        caldav_item["description"] = "\n".join(tw_item["annotations"])

    # uuid
    caldav_item["x-syncall-tw-uuid"] = f'{tw_item["uuid"]}'

    # Status
    caldav_item["status"] = aliases_tw_caldav_status[tw_item["status"]]

    # Priority
    if "priority" in tw_item:
        caldav_item["priority"] = aliases_tw_caldav_priority[tw_item["priority"].lower()]

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
        if "x-syncall-tw-uuid" in caldav_item.keys():
            tw_item["uuid"] = UUID(caldav_item["x-syncall-tw-uuid"])

    # Status
    tw_item["status"] = aliases_caldav_tw_status[caldav_item["status"]]

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
