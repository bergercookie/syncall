"""Asana-related utils."""

import datetime

import dateutil
from bubop import format_datetime_tz, format_dict, logger, parse_datetime

from syncall.asana.asana_task import AsanaTask
from syncall.types import TwItem


def convert_tw_to_asana(tw_item: TwItem) -> AsanaTask:
    # Extract Taskwarrior fields
    tw_description = tw_item["description"]
    tw_due = None
    if "due" in tw_item:
        tw_due = tw_item["due"]
    tw_end = None
    if "end" in tw_item:
        tw_end = tw_item["end"]
    tw_entry = tw_item["entry"]
    tw_modified = tw_item["modified"]
    tw_status = tw_item["status"]

    # Declare Asana fields
    as_completed = False
    as_completed_at = None
    as_created_at = None
    as_due_at = None
    as_due_on = None
    as_modified_at = None
    as_name = None

    # Convert Taskwarrior fields to Asana fields
    if tw_status == "completed":
        as_completed = True

        if tw_end is not None:
            if isinstance(tw_end, datetime.datetime):
                as_completed_at = tw_end
            else:
                as_completed_at = parse_datetime(tw_end)

    if not isinstance(tw_entry, datetime.datetime):
        as_created_at = parse_datetime(tw_entry)
    else:
        as_created_at = tw_entry

    if tw_due is not None:
        if isinstance(tw_due, datetime.datetime):
            as_due_at = tw_due
        else:
            as_due_at = parse_datetime(tw_due)
        as_due_on = as_due_at.date()

    if isinstance(tw_modified, datetime.datetime):
        as_modified_at = tw_modified
    else:
        as_modified_at = parse_datetime(tw_modified)

    as_name = tw_description

    # Build Asana task
    return AsanaTask(
        completed=as_completed,
        completed_at=as_completed_at,
        created_at=as_created_at,
        due_at=as_due_at,
        due_on=as_due_on,
        modified_at=as_modified_at,
        name=as_name,
    )


def convert_asana_to_tw(asana_task: AsanaTask) -> TwItem:
    # Extract Asana fields
    as_completed = asana_task["completed"]
    as_completed_at = asana_task["completed_at"]
    as_created_at = asana_task["created_at"]
    as_due_at = asana_task["due_at"]
    as_due_on = asana_task["due_on"]
    as_modified_at = asana_task["modified_at"]
    as_name = asana_task["name"]

    # Declare Taskwarrior fields
    tw_completed = None
    tw_due = tw_item = None
    tw_end = None
    tw_entry = None
    tw_modified = None
    tw_status = "pending"

    # Convert Asana fields to Taskwarrior fields
    if isinstance(as_created_at, datetime.datetime):
        tw_entry = as_created_at
    else:
        tw_entry = parse_datetime(as_created_at)

    if as_completed:
        if isinstance(as_completed_at, datetime.datetime):
            tw_end = as_completed_at
        else:
            tw_end = parse_datetime(as_completed_at)
        tw_status = "completed"

    if as_modified_at is not None:
        if isinstance(as_modified_at, datetime.datetime):
            tw_modified = as_modified_at
        else:
            tw_modified = parse_datetime(as_modified_at)

    # Asana may give us either 'due_at' (contains time and zone) or 'due_on'
    # (contains neither).
    if as_due_at is not None:
        if isinstance(as_due_at, datetime.datetime):
            tw_due = as_due_at
        else:
            tw_due = parse_datetime(as_due_at)
    elif as_due_on is not None:
        if isinstance(as_due_on, datetime.date):
            tw_due = datetime.datetime.combine(
                as_due_on, datetime.time(0, 0, 0), dateutil.tz.tzlocal()
            )
        else:
            tw_due = parse_datetime(as_due_on)

    tw_description = as_name

    tw_task = {
        "description": tw_description,
        "due": None,
        "end": tw_end,
        "entry": tw_entry,
        "modified": tw_modified,
        "status": tw_status,
    }

    if tw_due is not None:
        tw_task["due"] = tw_due

    if tw_modified is not None:
        tw_task["modified"] = tw_modified

    return tw_task
