"""Asana-related utils."""
import datetime
import logging

from bubop import parse_datetime

from syncall.cattr.cattr_task import CattrTask
from syncall.types import TwItem

logger = logging.getLogger(__name__)

def convert_tw_to_cattr(tw_item: TwItem) -> CattrTask:
    # Extract Taskwarrior fields
    logger.info(tw_item)
    with open("log.log","w") as f:
        print(tw_item,file=f)
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

    # Declare Cattr fields
    start_date = None
    due_date = None
    users = None
    project_phasae_id = None
    project_id = None
    task_name = tw_item['description']
    description = None
    important=False
    priority_id=None
    status_id=None
    project_name=tw_item.get("project", None)


    # Convert Taskwarrior fields to Asana fields
    if tw_status == "completed":
        status_id = 2

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
        date = tw_due if isinstance(tw_due, datetime.datetime) else parse_datetime(tw_due)
        due_date=date.strftime("%Y-%m-%d")
    task_name = tw_description

    # Build Cattr task
    ct = CattrTask(
        start_date=start_date,
        due_date=due_date,
        task_name=task_name,
        project_name=project_name,
        url=tw_item["uuid"],
        users=None,
        project_phase_id=None,
        project_id=None,
        description=None,
        important=None,
        priority_id=None,
        status_id=status_id,
        id=None,
        assigned_by=None,
        created_at=None,
        updated_at=None,
        deleted_at=None,
        relative_position=None,
        estimate=None,
    )
    print(ct)
    return ct


def convert_cattr_to_tw(cattr_task: CattrTask) -> TwItem:  # noqa: PLR0912
    logger.info("Hello")
    # Extract Cattr fields
    ct_completed = cattr_task["status_id"]==2
    ct_completed_at = cattr_task["deleted_at"]
    ct_completed_on=None
    ct_created_at = cattr_task["created_at"]
    ct_due_at = cattr_task["due_date"]
    ct_modified_at = cattr_task["updated_at"]
    ct_name = cattr_task["task_name"]

    # Declare Taskwarrior fields
    tw_due = None
    tw_end = None
    tw_entry = None
    tw_modified = None
    tw_status = "pending"

    # Convert Asana fields to Taskwarrior fields
    if isinstance(ct_created_at, datetime.datetime):
        tw_entry = ct_created_at
    else:
        tw_entry = parse_datetime(ct_created_at)

    if ct_completed and cattr_task['deleted_at']:
        if isinstance(ct_completed_at, datetime.datetime):
            tw_end = ct_completed_at
        else:
            tw_end = parse_datetime(ct_completed_at)
        tw_status = "completed"

    if ct_modified_at is not None:
        if isinstance(ct_modified_at, datetime.datetime):
            tw_modified = ct_modified_at
        else:
            tw_modified = parse_datetime(ct_modified_at)

    # Asana may give us either 'due_at' (contains time and zone) or 'due_on'
    # (contains neither).
    if ct_due_at is not None:
        if isinstance(ct_due_at, datetime.datetime):
            tw_due = ct_due_at
        else:
            tw_due = parse_datetime(ct_due_at)

    tw_description = ct_name

    tw_task = {
        "description": tw_description,
        "due": None,
        "end": tw_end,
        "entry": tw_entry,
        "modified": tw_modified,
        "status": tw_status,
    }
    logger.info(tw_task)

    try:
        if tw_due is not None:
            tw_task["due"] = tw_due

        if tw_modified is not None:
            tw_task["modified"] = tw_modified

    except Exception as err:
        print(cattr_task,Exception, err)
    return {
            "description": tw_description,
            "due": tw_due,
            "end": tw_end,
            "entry": tw_entry,
            "modified": tw_modified,
            "status": tw_status,
        }
