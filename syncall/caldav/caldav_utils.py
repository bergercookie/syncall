# ruff: noqa: PLR2004

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Sequence
from uuid import UUID

from bubop import logger

if TYPE_CHECKING:
    import caldav
    from icalendar.prop import vCategory
    from item_synchronizer.resolution_strategy import Item


def icalendar_component(obj: caldav.CalendarObjectResource):
    """Get the .icalendar_component isn't picked up by linters

    Ignore the warning when accessing it.
    """
    return obj.icalendar_component  # type: ignore


def calendar_todos(calendar: caldav.Calendar) -> Sequence[caldav.CalendarObjectResource]:
    return calendar.todos(include_completed=True)


def _parse_vcategory(vcategory: vCategory) -> Sequence[str]:
    return [str(category) for category in vcategory.cats]


def map_ics_to_item(vtodo) -> dict:
    """Extract the relevant info from an icalendar_component into a python dict."""
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
    todo_item["uuid"] = _convert_one("x-syncall-tw-uuid")

    for date_field in ("due", "created", "completed", "last-modified"):
        if vtodo.get(date_field):
            todo_item[date_field] = vtodo[date_field].dt

    vcategories = vtodo.get("categories")
    if vcategories is not None:
        # categories might be a vCategory containing the category names (strings) or might
        # return a List[vCategory], each vCategory with a single name
        # Option 1:
        #
        # | CATEGORIES:bugwarrior
        # | CATEGORIES:github_working_on_it
        # | CATEGORIES:programming
        # | CATEGORIES:remindme
        #
        # Option 2:
        # | CATEGORIES:bugwarrior,github_bug,github_help_wanted,github_tw_gcal_sync,pro
        all_categories = []
        if isinstance(vcategories, Sequence):
            for vcategory in vcategories:
                all_categories.extend(_parse_vcategory(vcategory))
        else:
            all_categories = [str(category) for category in vtodo["categories"].cats]
        todo_item["categories"] = all_categories

    return todo_item


def parse_caldav_item_desc(
    caldav_item: Item,
) -> tuple[list[str], UUID | None]:
    """Parse and return the necessary TW fields off a caldav Item.

    Pretty much directly copied from tw_gcal_utils, however we handle status differently, so only return annotations/uuid
    """
    annotations: list[str] = []
    uuid = None

    if "description" not in caldav_item.keys():
        return annotations, uuid

    caldav_desc = caldav_item["description"]
    # strip whitespaces, empty lines
    lines = [line.strip() for line in caldav_desc.split("\n") if line][1:]

    # annotations
    _i = 0
    for _i, line in enumerate(lines):
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
            annotations.append(parts[1].strip())
        else:
            break

    if _i == len(lines):
        return annotations, uuid

    # Iterate through rest of lines, find only the uuid
    for line in lines[_i:]:
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* uuid"):
            try:
                uuid = UUID(parts[1].strip())
            except ValueError as err:
                logger.error(
                    f'Invalid UUID "{err}" provided during caldav -> TW conversion,'
                    f" Using None...\n\n{traceback.format_exc()}",
                )

    return annotations, uuid
