import traceback
from typing import List, Optional, Tuple
from uuid import UUID

from bubop import logger
from item_synchronizer.types import Item

from syncall.google.gtasks_side import GTasksSide


def convert_tw_to_gtask(
    tw_item: Item,
    prefer_scheduled_date: bool = False,
) -> Item:
    """TW -> GTasks Converter.

    .. note:: Do not convert the ID as that may change either manually or
              after marking the task as "DONE"
    """
    assert all(
        i in tw_item.keys() for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    gtasks_item = {}

    # Title
    gtasks_item["title"] = tw_item["description"]

    # Status
    gtasks_item["status"] = "needsAction" if tw_item["status"] == "pending" else "completed"

    # Notes
    gtasks_item["notes"] = ""

    if "annotations" in tw_item.keys() and len(tw_item["annotations"]) > 0:
        for i, annotation in enumerate(tw_item["annotations"]):
            gtasks_item["notes"] += f"\n* Annotation {i + 1}: {annotation}"

    for k in [
        "status",
        "uuid",
    ]:  # NOTE(kisseliov): is notes the only place for tw status and description?
        gtasks_item["notes"] += f"\n* {k}: {tw_item[k]}"

    date_keys = ["scheduled", "due"] if prefer_scheduled_date else ["due", "scheduled"]

    # handle dates  ---------------------------------------------------------------------------
    # walk through the date_keys using the first of them that's present in the item at hand.
    # - if 'scheduled' date is prefered we set task due date to scheduled
    # - if 'due' date is present we set task due date to it
    # - otherwise we don't set due date at all
    for date_key in date_keys:
        if date_key in tw_item.keys():
            logger.trace(
                f'Using "{date_key}" date for {tw_item["uuid"]} for setting the due date of'
                " the task"
            )
            gtasks_item["due"] = GTasksSide.format_datetime(
                GTasksSide.parse_datetime(tw_item[date_key])
            )
            break

    # update time
    if "modified" in tw_item.keys():
        gtasks_item["updated"] = GTasksSide.format_datetime(
            GTasksSide.parse_datetime(tw_item["modified"])
        )

    return gtasks_item


def convert_gtask_to_tw(
    gtasks_item: Item,
    set_scheduled_date: bool = False,
) -> Item:
    """GTasks -> TW Converter.

    If set_scheduled_date, then it will set the "scheduled" date of the produced TW task
    instead of the "due" date
    """

    # Parse the description
    annotations, status, uuid = _parse_gtask_notes(gtasks_item)
    assert isinstance(annotations, list)
    assert isinstance(status, str)
    assert isinstance(uuid, UUID) or uuid is None

    tw_item: Item = {}
    # annotations
    tw_item["annotations"] = annotations

    # alias - make aliases dict?
    if status == "completed":
        status = "completed"

    if status == "needsAction":
        status = "pending"

    # Status
    if status not in ["pending", "completed", "deleted", "waiting", "recurring"]:
        logger.error(
            "Invalid status {status} in GCal->TW conversion of item. Skipping status:"
        )
    else:
        tw_item["status"] = status

    # uuid - may just be created -, thus not there
    if uuid is not None:
        tw_item["uuid"] = uuid

    # Description
    tw_item["description"] = gtasks_item["title"]

    # don't meddle with the 'entry' field
    if set_scheduled_date:
        date_key = "scheduled"
    else:
        date_key = "due"

    end_time = GTasksSide.get_task_completed_time(gtasks_item)
    tw_item[date_key] = end_time

    # update time
    if "updated" in gtasks_item.keys():
        tw_item["modified"] = GTasksSide.parse_datetime(gtasks_item["updated"])

    # NOTE(kisseliov): consider adding custom UDAs for Google Tasks to handle positions and hierarchy
    return tw_item


def _parse_gtask_notes(
    gtasks_item: Item,
) -> Tuple[List[str], str, Optional[UUID]]:
    """Parse and return the necessary TW fields off a Google Tasks task notes."""
    annotations: List[str] = []
    status = "pending"
    uuid = None

    if "notes" not in gtasks_item.keys():
        return annotations, status, uuid

    gtask_description = gtasks_item["notes"]
    # strip whitespaces, empty lines
    lines = [line.strip() for line in gtask_description.split("\n") if line]

    # annotations
    i = 1
    for i, line in enumerate(lines):
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
            annotations.append(parts[1].strip())
        else:
            break

    if i == len(lines) - 1:
        return annotations, status, uuid

    # Iterate through rest of lines, find only the status and uuid ones
    for line in lines[i:]:
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2:
            start = parts[0].lower()
            if start.startswith("* status"):
                status = parts[1].strip().lower()
            elif start.startswith("* uuid"):
                try:
                    uuid = UUID(parts[1].strip())
                except ValueError as err:
                    logger.error(
                        f'Invalid UUID "{err}" provided during GTask -> TW conversion,'
                        f" Using None...\n\n{traceback.format_exc()}"
                    )

    return annotations, status, uuid
