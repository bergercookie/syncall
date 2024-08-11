# ruff: noqa: PLR2004

"""Miscellaneous TW related utilities.

At the time of writing, these are primarily used in the TW<>Gtasks and TW<>Gcal integrations.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Sequence
from uuid import UUID

from bubop import logger

if TYPE_CHECKING:
    from syncall.types import TwItem


def get_tw_annotations_as_str(tw_item: TwItem) -> str:
    """Return all the annotations of the given object in a single string.

    Put each annotation in its own line and prefix it with "Annotation X" where X is an
    increasing integer id.

    Return an empty string if there are no annotations.
    """
    if "annotations" in tw_item and len(tw_item["annotations"]) > 0:
        annotations_li = [
            f"* Annotation {i + 1}: {annotation}"
            for i, annotation in enumerate(tw_item["annotations"])
        ]

        return "\n".join(annotations_li)

    return ""


def get_tw_status_and_uuid_as_str(tw_item: TwItem) -> str:
    """Return the UUID and status of the given TW item in a single string."""
    return "\n".join(
        [
            f"{k}: {tw_item[k]}"
            for k in [
                "status",
                "uuid",
            ]
        ],
    )


def extract_tw_fields_from_string(s: str) -> tuple[Sequence[str], str, UUID | None]:
    """Parse the TW annotations, status, and UUID fields from the given string."""
    annotations = []
    status = "pending"
    uuid = None

    # strip whitespaces, empty lines
    lines = [line.strip() for line in s.split("\n") if line][0:]
    _i = 0
    for _i, line in enumerate(lines):
        parts = line.split(":", maxsplit=1)
        if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
            annotations.append(parts[1].strip())
        else:
            break

    if _i == len(lines) - 1:
        return annotations, status, uuid

    # Iterate through rest of lines, find only the status and uuid ones
    for line in lines[_i:]:
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
                        f'Invalid UUID "{err}" provided during the conversion to taskwarrior,'
                        f" Using None...\n\n{traceback.format_exc()}",
                    )

    return annotations, status, uuid
