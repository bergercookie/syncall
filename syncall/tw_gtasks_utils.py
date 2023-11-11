from bubop import logger
from item_synchronizer.types import Item

from syncall.google.gtasks_side import GTasksSide
from syncall.tw_utils import extract_tw_fields_from_string, get_tw_annotations_as_str
from syncall.types import GTasksItem


def convert_tw_to_gtask(
    tw_item: Item,
) -> Item:
    """TW -> GTasks conversion."""
    assert all(
        i in tw_item.keys() for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    gtasks_item = {}

    # title
    gtasks_item["title"] = tw_item["description"]

    # status
    gtasks_item["status"] = "needsAction" if tw_item["status"] == "pending" else "completed"

    # notes
    if annotations_str := get_tw_annotations_as_str(tw_item):
        gtasks_item["notes"] = annotations_str

    # update time
    if "modified" in tw_item.keys():
        gtasks_item["updated"] = GTasksSide.format_datetime(
            GTasksSide.parse_datetime(tw_item["modified"])
        )

    return gtasks_item


def convert_gtask_to_tw(
    gtasks_item: GTasksItem,
    set_scheduled_date: bool = False,
) -> Item:
    """GTasks -> TW Converter.

    If set_scheduled_date, then it will set the "scheduled" date of the produced TW task
    instead of the "due" date
    """

    # Parse the description
    annotations = []
    uuid = None
    if (section := gtasks_item.get("notes")) is not None:
        annotations, _, uuid = extract_tw_fields_from_string(section)

    tw_item: Item = {}
    # annotations
    tw_item["annotations"] = annotations

    gtasks_to_tw_status_corrs = {
        "completed": "completed",
        "needsAction": "pending",
    }

    status_gtask = gtasks_item["status"]
    status_tw = gtasks_to_tw_status_corrs.get(status_gtask)
    if status_tw is None:
        logger.error(
            f"Unknown Google Task status {status_gtask} for google task item {gtasks_item}."
            " Setting it to pending"
        )
        status_tw = "pending"

    # status
    tw_item["status"] = status_tw

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

    # due/scheduled date
    due_date = GTasksSide.get_task_due_time(gtasks_item)
    if due_date is not None:
        tw_item[date_key] = due_date

    # end date
    end_date = GTasksSide.get_task_completed_time(gtasks_item)
    if end_date is not None:
        tw_item["end"] = end_date

    # update time
    if "updated" in gtasks_item.keys():
        tw_item["modified"] = GTasksSide.parse_datetime(gtasks_item["updated"])

    return tw_item
