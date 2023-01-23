import traceback
from datetime import timedelta
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

import icalendar
from bubop import logger
from item_synchronizer.types import Item

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
    annotations, uuid = _parse_caldav_item_desc(caldav_item)
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


def parse_vcategory(vcategory: icalendar.prop.vCategory) -> Sequence[str]:
    return [str(category) for category in vcategory.cats]


def map_ics_to_item(vtodo) -> Dict:
    """
    Utility function that extracts the relevant info from an icalendar_component into a python
    dict
    """
    todo_item = {}
    todo_item["id"] = str(vtodo.get("uid"))

    def _convert_one(name: str) -> str:
        item = vtodo.get(name)
        if item:
            return str(item)

        return ""

    for name in ["status", "priority"]:
        todo_item[name] = _convert_one(name).lower()
    for name in ["description", "summary"]:
        todo_item[name] = _convert_one(name)

    for name in ["last-modified"]:
        item = vtodo.get(name)
        if item:
            todo_item[name] = item.dt

    if vtodo.get("due"):
        todo_item["due"] = vtodo["due"].dt

    vcategories = vtodo.get("categories")
    if vcategories is not None:
        # categories might be a vCategory containing the category names (strings) or might
        # return a List[vCategory], each vCategory with a single name
        # Option 1:
        #
        # CATEGORIES:bugwarrior
        # CATEGORIES:github_working_on_it
        # CATEGORIES:programming
        # CATEGORIES:remindme
        #
        # Option 2:
        # CATEGORIES:bugwarrior,github_bug,github_help_wanted,github_tw_gcal_sync,pro
        all_categories = []
        if isinstance(vcategories, Sequence):
            for vcategory in vcategories:
                all_categories.extend(parse_vcategory(vcategory))
        else:
            all_categories = [str(category) for category in vtodo["categories"].cats]
        todo_item["categories"] = all_categories

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

    caldav_desc = caldav_item["description"]
    # strip whitespaces, empty lines
    lines = [line.strip() for line in caldav_desc.split("\n") if line][1:]

    # annotations
    i = 0
    for i, line in enumerate(lines):
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
            annotations.append(parts[1].strip())
        else:
            break

    if i == len(lines):
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
