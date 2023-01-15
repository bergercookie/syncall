import traceback
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from bubop import logger
from item_synchronizer.types import Item

aliases_tw_caldav_status = {
    "completed": "completed",
    "pending": "needs-action",
    "waiting": "needs-action",
    "deleted": "cancelled",
}

aliases_tw_caldav_priority = {
    "l": 9,
    "m": 5,
    "h": 1,
}


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
    for k in ["uuid"]:
        caldav_item["description"] += f"\n* {k}: {tw_item[k]}"

    # Status
    caldav_item["status"] = aliases_tw_caldav_status[tw_item["status"]]

    # Priority
    if "priority" in tw_item.keys():
        caldav_item["priority"] = aliases_tw_caldav_priority[tw_item["priority"].lower()]

    # Timestamp - Don't mess around too much with created/updated keys
    if "modified" in tw_item.keys():
        caldav_item["last-modified"] = tw_item["modified"]

    # Start/due dates
    # - If given due date -> (start=due-1, end=due)
    if "due" in tw_item.keys():
        caldav_item["start"] = tw_item["due"] - timedelta(hours=1)
        caldav_item["due"] = tw_item["due"]

    if "tags" in tw_item.keys():
        caldav_item["categories"] = tw_item["tags"]

    return caldav_item


def convert_caldav_to_tw(caldav_item: Item) -> Item:
    # Parse the description
    annotations, uuid = _parse_caldav_item_desc(caldav_item)
    assert isinstance(annotations, list)
    assert isinstance(uuid, UUID) or uuid is None

    tw_item: Item = {}

    tw_item["description"] = caldav_item.get("summary")
    tw_item["annotations"] = annotations
    if uuid is not None:
        tw_item["uuid"] = uuid

    # Status
    tw_item["status"] = next(
        key
        for key, value in aliases_tw_caldav_status.items()
        if caldav_item["status"] == value
    )

    # Priority
    if caldav_item.get("priority"):
        priority = next(
            (
                key
                for key, value in aliases_tw_caldav_priority.items()
                if caldav_item["priority"] == value
            ),
            None,
        )
        if priority:
            tw_item["priority"] = priority

    # Timestamps
    if "last-modified" in caldav_item.keys():
        tw_item["modified"] = caldav_item["last-modified"]

    # Start/due dates
    if "due" in caldav_item.keys():
        tw_item["due"] = caldav_item["due"]

    if "categories" in caldav_item.keys():
        tw_item["tags"] = caldav_item["categories"]

    return tw_item


def map_ics_to_item(vtodo) -> Dict:
    """
    Utility class that will extract the relevant info from an icalendar_component into a python dict
    """
    todo_item = {}
    todo_item["id"] = str(vtodo.get("uid"))
    for i in ["status", "priority", "description", "summary"]:
        item = vtodo.get(i)
        if item:
            todo_item[i] = str(item).lower()
    for i in ["created", "last-modified"]:
        item = vtodo.get(i)
        if item:
            todo_item[i] = item.dt

    if vtodo.get("due"):
        todo_item["due"] = vtodo["due"].dt

    if vtodo.get("categories"):
        todo_item["categories"] = [str(category) for category in vtodo["categories"].cats]

    return todo_item


def _parse_caldav_item_desc(
    caldav_item: Item,
) -> Tuple[List[str], Optional[UUID]]:
    """
    Parse and return the necessary TW fields off a caldav Item.

    Pretty much directly copied from tw_gcal_utils, however we handle status differently, so only return annotations/uuid
    """
    annotations: List[str] = []
    uuid = None

    if "description" not in caldav_item.keys():
        return annotations, uuid

    gcal_desc = caldav_item["description"]
    # strip whitespaces, empty lines
    lines = [line.strip() for line in gcal_desc.split("\n") if line][1:]

    # annotations
    i = 0
    for i, line in enumerate(lines):
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
            annotations.append(parts[1].strip())
        else:
            break

    if i == len(lines) - 1:
        return annotations, uuid

    # Iterate through rest of lines, find only the uuid
    for line in lines[i:]:
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* uuid"):
            try:
                uuid = UUID(parts[1].strip())
            except ValueError as err:
                logger.error(
                    f'Invalid UUID "{err}" provided during caldav -> TW conversion,'
                    f" Using None...\n\n{traceback.format_exc()}"
                )

    return annotations, uuid
