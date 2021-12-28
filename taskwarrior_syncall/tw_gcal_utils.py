import traceback
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from bubop import logger
from item_synchronizer.types import Item

from taskwarrior_syncall.google.gcal_side import GCalSide

_prefix_title_done_str = "✅"


def convert_tw_to_gcal(tw_item: Item) -> Item:
    """TW -> GCal Converter.

    .. note:: Do not convert the ID as that may change either manually or
              after marking the task as "DONE"
    """
    assert all(
        i in tw_item.keys() for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    gcal_item = {}

    # Summary
    gcal_item["summary"] = tw_item["description"]
    if tw_item["status"] == "completed" and not gcal_item["summary"].startswith(
        _prefix_title_done_str
    ):
        gcal_item["summary"] = f'{_prefix_title_done_str}{gcal_item["summary"]}'

    # description
    gcal_item["description"] = "IMPORTED FROM TASKWARRIOR\n"
    if "annotations" in tw_item.keys():
        for i, annotation in enumerate(tw_item["annotations"]):
            gcal_item["description"] += f"\n* Annotation {i + 1}: {annotation}"

    gcal_item["description"] += "\n"
    for k in ["status", "uuid"]:
        gcal_item["description"] += f"\n* {k}: {tw_item[k]}"

    # Handle dates:
    # - If given due date -> (start=due-1, end=due)
    # - Else -> (start=entry, end=entry+1)
    if "due" in tw_item.keys():
        due_dt_gcal = GCalSide.format_datetime(tw_item["due"])
        gcal_item["start"] = {
            "dateTime": GCalSide.format_datetime(tw_item["due"] - timedelta(hours=1))
        }
        gcal_item["end"] = {"dateTime": due_dt_gcal}
    else:
        entry_dt = tw_item["entry"]
        entry_dt_gcal_str = GCalSide.format_datetime(entry_dt)

        gcal_item["start"] = {"dateTime": entry_dt_gcal_str}

        gcal_item["end"] = {
            "dateTime": GCalSide.format_datetime(entry_dt + timedelta(hours=1))
        }

    # update time
    if "modified" in tw_item.keys():
        gcal_item["updated"] = GCalSide.format_datetime(tw_item["modified"])

    return gcal_item


def convert_gcal_to_tw(gcal_item: Item) -> Item:
    """GCal -> TW Converter."""

    # Parse the description
    annotations, status, uuid = _parse_gcal_item_desc(gcal_item)
    assert isinstance(annotations, list)
    assert isinstance(status, str)
    assert isinstance(uuid, UUID) or uuid is None

    tw_item: Item = {}
    # annotations
    tw_item["annotations"] = annotations

    # alias - make aliases dict?
    if status == "done":
        status = "completed"

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
    gcal_summary = gcal_item["summary"]
    if gcal_summary.startswith(_prefix_title_done_str):
        gcal_summary = gcal_summary[len(_prefix_title_done_str) :]
    tw_item["description"] = gcal_summary

    # don't meddle with the 'entry' field
    if isinstance(gcal_item["end"], datetime):
        tw_item["due"] = gcal_item["end"]
    else:
        tw_item["due"] = GCalSide.get_event_time(gcal_item, t="end")

    # update time
    if "updated" in gcal_item.keys():
        tw_item["modified"] = GCalSide.parse_datetime(gcal_item["updated"])

    # Note:
    # Don't add extra fields of GCal as TW annotations because then, if converted
    # backwards, these annotations are going in the description of the Gcal event and then
    # these are going into the event description and this happens on every conversion. Add
    # them as new TW UDAs if needed

    return tw_item


def _parse_gcal_item_desc(
    gcal_item: Item,
) -> Tuple[List[str], str, Optional[UUID]]:
    """Parse and return the necessary TW fields off a Google Calendar Item."""
    annotations: List[str] = []
    status = "pending"
    uuid = None

    if "description" not in gcal_item.keys():
        return annotations, status, uuid

    gcal_desc = gcal_item["description"]
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
                        f'Invalid UUID "{err}" provided during GCal -> TW conversion,'
                        f" Using None...\n\n{traceback.format_exc()}"
                    )

    return annotations, status, uuid
