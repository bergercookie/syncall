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
        i in tw_item.keys() for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    caldav_item: Item = {}

    caldav_item["summary"] = tw_item["description"]
    # description
    caldav_item["description"] = "IMPORTED FROM TASKWARRIOR\n"
    if "annotations" in tw_item.keys():
        for i, annotation in enumerate(tw_item["annotations"]):
            caldav_item["description"] += f"\n* Annotation {i + 1}: {annotation}"

    caldav_item["description"] += "\n"
    caldav_item["description"] += f'\n* uuid: {tw_item["uuid"]}'

    # Status
    caldav_item["status"] = aliases_tw_caldav_status[tw_item["status"]]

    # Priority
    if "priority" in tw_item.keys():
        caldav_item["priority"] = aliases_tw_caldav_priority[tw_item["priority"].lower()]

    # Timestamps
    if "entry" in tw_item.keys():
        caldav_item["created"] = tw_item["entry"]
    if "end" in tw_item.keys():
        caldav_item["completed"] = tw_item["end"]
    if "modified" in tw_item.keys():
        caldav_item["last-modified"] = tw_item["modified"]

    # Start/due dates
    # - If given due date -> (start=due-1, end=due)
    if "due" in tw_item.keys():
        caldav_item["start"] = tw_item["due"] - timedelta(hours=1)
        caldav_item["due"] = tw_item["due"]

    if "tags" in tw_item.keys():
        caldav_item["categories"] = tw_item["tags"]

    # if start-ed, override the status appropriately
    if "start" in tw_item.keys():
        caldav_item["status"] = "in-process"

    return caldav_item


def convert_caldav_to_tw(caldav_item: Item) -> Item:
    # Parse the description
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
    if uuid is not None:
        tw_item["uuid"] = uuid

    # Status
    tw_item["status"] = aliases_caldav_tw_status[caldav_item["status"]]

    # Priority
    prio = aliases_caldav_tw_priority.get(caldav_item["priority"])
    if prio:
        tw_item["priority"] = prio

    # Timestamps
    if "created" in caldav_item.keys():
        tw_item["entry"] = caldav_item["created"]
    if "completed" in caldav_item.keys():
        tw_item["end"] = caldav_item["completed"]
    if "last-modified" in caldav_item.keys():
        tw_item["modified"] = caldav_item["last-modified"]

    # Start/due dates
    if "due" in caldav_item.keys():
        tw_item["due"] = caldav_item["due"]

    if "categories" in caldav_item.keys():
        tw_item["tags"] = caldav_item["categories"]

    if caldav_item["status"] == "in-process" and "last-modified" in caldav_item:
        tw_item["start"] = caldav_item["last-modified"]

    return tw_item
