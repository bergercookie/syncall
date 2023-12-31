from datetime import timedelta
from uuid import UUID

from bubop import logger
from item_synchronizer.types import Item

from syncall.google.gcal_side import GCalSide
from syncall.taskwarrior.taskw_duration import (
    convert_tw_duration_to_timedelta,
    taskw_duration_serialize,
    tw_duration_key,
)
from syncall.tw_utils import (
    extract_tw_fields_from_string,
    get_tw_annotations_as_str,
    get_tw_status_and_uuid_as_str,
)
from syncall.types import GCalItem

_prefix_title_success_str = "✅"
_prefix_title_failed_str = "❌"
_failed_str = "FAIL"


def _already_has_prefix(gcal_item: Item) -> bool:
    return gcal_item["summary"].startswith(_prefix_title_success_str) or gcal_item[
        "summary"
    ].startswith(_prefix_title_failed_str)


def _add_task_prefix_if_not_present(gcal_item: Item):
    if _already_has_prefix(gcal_item):
        return
    if gcal_item["summary"].startswith(_failed_str):
        _add_failed_prefix(gcal_item)
    else:
        _add_success_prefix(gcal_item)


def _add_success_prefix(gcal_item: Item):
    gcal_item["summary"] = f'{_prefix_title_success_str}{gcal_item["summary"]}'


def _add_failed_prefix(gcal_item: Item):
    gcal_item[
        "summary"
    ] = f'{_prefix_title_failed_str}{gcal_item["summary"][len(_failed_str)+1:]}'


def convert_tw_to_gcal(
    tw_item: Item,
    prefer_scheduled_date: bool = False,
    default_event_duration: timedelta = timedelta(hours=1),
) -> Item:
    """TW -> GCal conversion."""
    assert all(
        i in tw_item.keys() for i in ("description", "status", "uuid")
    ), "Missing keys in tw_item"

    gcal_item = {}

    # Summary
    gcal_item["summary"] = tw_item["description"]
    if tw_item["status"] == "completed":
        _add_task_prefix_if_not_present(gcal_item=gcal_item)

    # description
    gcal_item["description"] = "IMPORTED FROM TASKWARRIOR\n"
    gcal_item["description"] += "\n".join(
        [get_tw_annotations_as_str(tw_item), get_tw_status_and_uuid_as_str(tw_item)]
    )

    date_keys = ["scheduled", "due"] if prefer_scheduled_date else ["due", "scheduled"]
    # event duration --------------------------------------------------------------------------
    # use the UDA field to fetch the duration of the event, otherwise fallback to the default
    # duration
    convert_tw_duration_to_timedelta(tw_item)

    # handle start, end datetimes -------------------------------------------------------------
    # walk through the date_keys using the first of them that's present in the item at hand.
    # - if the prefered key is `scheduled` use the item["scheduled"] as the prefered date and
    #   create an event with (start=scheduled-duration, end=scheduled).
    # - if the preferred key is due, create an event with (start=due-duration, end=due)
    # - if there's no due and no scheduled dates assigned, use the entry key: (start=entry,
    # end=entry+duration)
    for date_key in date_keys:
        if date_key in tw_item.keys():
            logger.trace(
                f'Using "{date_key}" date for {tw_item["uuid"]} for setting the end date of'
                " the event"
            )
            dt_gcal = GCalSide.format_datetime(tw_item[date_key])
            gcal_item["start"] = {
                "dateTime": GCalSide.format_datetime(
                    tw_item[date_key] - tw_item[tw_duration_key]
                )
            }
            gcal_item["end"] = {"dateTime": dt_gcal}
            break
    else:
        logger.trace(
            f'Using "entry" date for {tw_item["uuid"]} for setting the start date of the event'
        )
        entry_dt = tw_item["entry"]
        entry_dt_gcal_str = GCalSide.format_datetime(entry_dt)

        gcal_item["start"] = {"dateTime": entry_dt_gcal_str}

        gcal_item["end"] = {
            "dateTime": GCalSide.format_datetime(entry_dt + tw_item[tw_duration_key])
        }

    return gcal_item


def convert_gcal_to_tw(
    gcal_item: GCalItem,
    set_scheduled_date: bool = False,
) -> Item:
    """GCal -> TW Converter.

    If set_scheduled_date, then it will set the "scheduled" date of the produced TW task
    instead of the "due" date
    """

    # Parse the description
    annotations = []
    status = "pending"
    uuid = None
    if (section := gcal_item.get("description")) is not None:
        annotations, status, uuid = extract_tw_fields_from_string(section)

    assert isinstance(annotations, list)
    assert isinstance(status, str)
    assert isinstance(uuid, UUID) or uuid is None

    tw_item: Item = {}
    # annotations
    tw_item["annotations"] = annotations

    if status == "done":
        status = "completed"

    # Status
    if status not in ["pending", "completed", "deleted", "waiting", "recurring"]:
        logger.error(
            f"Invalid status {status} in GCal->TW conversion of item. Skipping status:"
        )
    else:
        tw_item["status"] = status

    # uuid - may just be created -, thus not there
    if uuid is not None:
        tw_item["uuid"] = uuid

    # Description
    gcal_summary = gcal_item["summary"]
    if gcal_summary.startswith(_prefix_title_success_str):
        gcal_summary = gcal_summary[len(_prefix_title_success_str) :]
    tw_item["description"] = gcal_summary

    # don't meddle with the 'entry' field
    if set_scheduled_date:
        date_key = "scheduled"
    else:
        date_key = "due"

    end_time = GCalSide.get_event_time(gcal_item, t="end")

    tw_item[tw_duration_key] = taskw_duration_serialize(
        end_time - GCalSide.get_event_time(gcal_item, t="start")
    )

    tw_item[date_key] = end_time

    # Note:
    # Don't add extra fields of GCal as TW annotations because then, if converted
    # backwards, these annotations are going in the description of the GCal event and then
    # these are going into the event description and this happens on every conversion. Add
    # them as new TW UDAs if needed

    return tw_item
