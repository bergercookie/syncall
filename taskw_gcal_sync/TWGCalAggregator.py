from __future__ import annotations

import atexit
import os
import pickle
import sys
import traceback
from datetime import timedelta
from enum import Enum
from functools import cached_property, partial
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple, Union
from uuid import UUID

from bidict import bidict
from loguru import logger
from tqdm import tqdm

from taskw_gcal_sync import GCalSide, GenericSide, TaskWarriorSide
from taskw_gcal_sync.PrefsManager import PrefsManager

pickle_dump = partial(pickle.dump, protocol=0)


class ItemType(Enum):
    GCAL = "gcal"
    TW = "tw"

    @cached_property
    def other(self) -> ItemType:
        return _item_type_to_other[self]

    @cached_property
    def id_key(self) -> str:
        return _item_type_to_id_key[self]

    def __str__(self):
        return str(self.value)


_item_type_to_other = {
    ItemType.TW: ItemType.GCAL,
    ItemType.GCAL: ItemType.TW,
}

_item_type_to_id_key = {
    ItemType.TW: "uuid",
    ItemType.GCAL: "id",
}


class TypeStats:
    """Container class for printing execution stats on exit - per type."""

    def __init__(self, title: str):
        self._title = title

        self._created_new = 0
        self._updated = 0
        self._deleted = 0
        self._errors = 0

        self._sep = "-" * len(self._title)

    def create_new(self):
        self._created_new += 1

    def update(self):
        self._updated += 1

    def delete(self):
        self._deleted += 1

    def error(self):
        self._errors += 1

    def __str__(self) -> str:
        s = (
            f"{self._title}\n"
            f"{self._sep}\n"
            f"\t* Tasks created: {self._created_new}\n"
            f"\t* Tasks updated: {self._updated}\n"
            f"\t* Tasks deleted: {self._deleted}\n"
            f"\t* Errors:        {self._errors}\n"
        )
        return s


class TWGCalAggregator:
    """Aggregator class: TaskWarrior <-> Google Calendar sides.

    Having an aggregator is handy for managing push/pull/sync directives in a
    consistent manner.
    """

    def __init__(self, tw_config: dict, gcal_config: dict, **kargs):
        assert isinstance(tw_config, dict)
        assert isinstance(gcal_config, dict)

        # Preferences manager
        self.prefs_manager = PrefsManager("taskw_gcal_sync")

        # Own config
        self.config: Dict[str, Any] = {}

        self.config["tw_serdes_dir"] = Path(self.prefs_manager.prefs_dir_full) / "pickle_tw"
        self.config["gcal_serdes_dir"] = (
            Path(self.prefs_manager.prefs_dir_full) / "pickle_gcal"
        )
        self.config.update(**kargs)  # Update

        # initialise both sides
        tw_config_new = {}
        tw_config_new.update(tw_config)
        self.tw_side = TaskWarriorSide(**tw_config_new)

        gcal_config_new = {}
        gcal_config_new.update(gcal_config)
        self.gcal_side = GCalSide(**gcal_config_new)  # type: ignore

        self._report_stats = True
        self._stats = {
            ItemType.TW: TypeStats("TaskWarrior"),
            ItemType.GCAL: TypeStats("Google Calendar"),
        }
        # Correspondences between the TW reminders and the GCal events
        # For finding the matches: [TW] uuid <-> [GCal] id
        if "tw_gcal_ids" not in self.prefs_manager:
            self.prefs_manager["tw_gcal_ids"] = bidict()
        self.tw_gcal_ids = self.prefs_manager["tw_gcal_ids"]

        self.cleaned_up = False
        atexit.register(self.cleanup)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def start(self):
        self.tw_side.start()
        self.gcal_side.start()

        self.config["tw_serdes_dir"].mkdir(exist_ok=True)
        self.config["gcal_serdes_dir"].mkdir(exist_ok=True)

    def cleanup(self):
        """Method to be called automatically on instance destruction."""

        if not self.cleaned_up:
            # print summary stats
            if self._report_stats:
                logger.warning(f"\n{self._stats[ItemType.TW]}\n{self._stats[ItemType.GCAL]}")

            self.cleaned_up = True

    def register_items(self, items: Sequence[Dict[str, Any]], item_type: ItemType):
        """Register a list of items coming from the side of `item_type`.

        - Register in the broker
        - Add the corresponding item in the other form (TW if registering GCal
          event or the other way around)
        """
        registered_ids = (
            self.tw_gcal_ids if item_type is ItemType.TW else self.tw_gcal_ids.inverse
        )
        _, other_side = self._get_side_instances(item_type)
        convert_fun = (
            TWGCalAggregator.convert_tw_to_gcal
            if item_type is ItemType.TW
            else TWGCalAggregator.convert_gcal_to_tw
        )

        other_type = item_type.other
        serdes_dir, other_serdes_dir = self._get_serdes_dirs(item_type)
        other_stats = self._stats[item_type.other]

        logger.info(f"[{item_type}] Registering items at {other_type}...")
        for item in tqdm(items):
            id_ = str(item[item_type.id_key])

            # Check if I have this item in the register
            if id_ not in registered_ids.keys():
                # Create the item
                logger.info(f"[{item_type}] Inserting item at {other_type}, new id: {id_} ...")

                # Add it to TW/GCal
                item_converted = convert_fun(item)
                try:
                    other_item_created = other_side.add_item(item_converted)
                except KeyboardInterrupt:
                    raise
                except:
                    logger.error(
                        f'Adding item "{id_}" failed.\nItem'
                        f" contents:\n\n{item_converted}\n\nException:"
                        f"\n\n{traceback.format_exc()}"
                    )
                    other_stats.error()
                else:
                    #  Add registry entry
                    registered_ids[id_] = str(other_item_created[other_type.id_key])

                    # Cache both sides with pickle - f=id_
                    logger.debug(f'Pickling item "{id_}"')
                    logger.debug(f'Pickling item "{registered_ids[id_]}"')
                    pickle_dump(item, (serdes_dir / id_).open("wb"))
                    pickle_dump(
                        other_item_created,
                        (other_serdes_dir / registered_ids[id_]).open("wb"),
                    )

                    other_stats.create_new()

            else:
                # already in registry

                # Update item
                # TODO: if this fails might be because the user cleared only the pickle
                # directories and not the cfg file
                prev_item = pickle.load((serdes_dir / id_).open("rb"))

                # Unchanged item
                if not self.item_has_update(prev_item, item, item_type):
                    logger.debug(f"[{item_type}] Unchanged item, id: {id_} ...")
                    continue

                # Item has changed
                other_id = registered_ids[id_]
                other_item = other_side.get_item(other_id)
                assert other_item, f"{other_id} not found on other side"

                logger.info(
                    f"[{item_type}] Item has changed, id: {id_} | "
                    f"updating counterpart at {other_type}, id: {other_id} ..."
                )

                # Make sure that counterpart has not changed
                # otherwise deal with conflict
                prev_other_item = pickle.load((other_serdes_dir / other_id).open("rb"))
                if self.item_has_update(prev_other_item, other_item, other_type):
                    logger.warning(f"Conflict! Arbitrarily selecting [{item_type}]")

                # Convert to and update other side
                other_item_new = convert_fun(item)

                try:
                    other_side.update_item(other_id, **other_item_new)
                except KeyboardInterrupt:
                    raise
                except:
                    logger.error(
                        f'Updating item "{other_id}" failed.\nItem contents:'
                        f"\n\n{other_item_new}\n\nException: \n\n{traceback.format_exc()}\n"
                    )
                    other_stats.error()
                else:
                    # Update cached version
                    pickle_dump(item, (serdes_dir / id_).open("wb"))
                    pickle_dump(other_item_new, (other_serdes_dir / other_id).open("wb"))
                    other_stats.update()

    def _get_serdes_dirs(self, item_type: ItemType) -> Tuple[Path, Path]:
        serdes_dir = self.config[f"{item_type}_serdes_dir"]
        other_serdes_dir = self.config[f"{item_type.other}_serdes_dir"]

        return serdes_dir, other_serdes_dir

    def _get_side_instances(self, item_type: ItemType) -> Tuple[GenericSide, GenericSide]:
        side = self.tw_side if item_type is ItemType.TW else self.gcal_side
        other_side = self.gcal_side if item_type is ItemType.TW else self.tw_side

        return side, other_side

    def _remove_serdes_files(self, *paths):
        for p in paths:
            try:
                p.unlink()
            except FileNotFoundError:
                logger.warning(f"File {p} doesn't seem to exist anymore...")

    def synchronise_deleted_items(self, item_type: ItemType):
        """Synchronise a task deleted at the side of `item_type`.

        Deleted tasks are detected from cached entries in the items mapping that
        don't exist anymore in the side of `item_type`.

        :param item_type: "tw" / "gcal"
        """

        # iterate through all the cached mappings - verify that they exist in
        # the side (TW/GCal)
        registered_ids = (
            self.tw_gcal_ids if item_type is ItemType.TW else self.tw_gcal_ids.inverse
        )
        other_registered_ids = (
            self.tw_gcal_ids if item_type is ItemType.GCAL else self.tw_gcal_ids.inverse
        )
        side, other_side = self._get_side_instances(item_type)
        other_type = item_type.other
        serdes_dir, other_serdes_dir = self._get_serdes_dirs(item_type)
        other_stats = self._stats[item_type.other]

        logger.info(f"[{item_type}] Deleting items at {other_type}...")

        other_to_remove: List[str] = []
        for id_, other_id in registered_ids.items():
            item_side = side.get_item(id_)
            if item_side is not None:
                continue  # item is still there

            # item deleted
            logger.info(f"[{item_type}] Synchronising deleted item, id: {id_} ...")

            try:
                other_item = other_side.get_item(other_id)
                if not other_item:
                    logger.warning(
                        f"{other_id} not found at {item_type.other} side, maybe it was also"
                        " deleted?"
                    )
                    other_to_remove.append(other_id)
                    self._remove_serdes_files(serdes_dir / id_, other_serdes_dir / other_id)
                    other_stats.delete()
                    continue

                prev_other_item = pickle.load((other_serdes_dir / other_id).open("rb"))
                if self.item_has_update(prev_other_item, other_item, other_type):
                    logger.warning(
                        "Counterpart item, {other_id} has changed, proceeding with its"
                        " deletion though..."
                    )

                # delete item
                other_side.delete_single_item(other_id)

                # delete mapping
                other_to_remove.append(other_id)

                # remove serdes files
                self._remove_serdes_files(serdes_dir / id_, other_serdes_dir / other_id)
                other_stats.delete()
            except KeyError:
                logger.error(
                    "Item to delete [{id_}] is not present."
                    f"\n\n{other_item}\n\nException: {traceback.format_exc()}\n"
                )
                other_stats.error()
            except KeyboardInterrupt:
                raise
            except:
                logger.error(
                    'Deleting item "{id_}" failed.\nItem contents:'
                    f"\n\n{other_item}\n\nException: {traceback.format_exc}\n"
                )
                other_stats.error()

        # Remove ids (out of loop)
        for other_id in other_to_remove:
            other_registered_ids.pop(other_id)

    def item_has_update(self, prev_item: dict, new_item: dict, item_type: ItemType) -> bool:
        """Determine whether the item has been updated."""
        side, _ = self._get_side_instances(item_type)
        return not side.items_are_identical(
            prev_item, new_item, ignore_keys=["urgency", "modified", "updated"]
        )

    # currently unused.
    @staticmethod
    def compare_tw_gcal_items(
        tw_item: dict, gcal_item: dict
    ) -> Tuple[Set[str], Dict[str, Tuple[Any, Any]]]:
        """Compare a TW and a GCal item and find any differences.

        :returns: list of different keys and Dictionary with the differences for
                  same keys
        """
        # Compare in TW form
        tw_item_out = TWGCalAggregator.convert_gcal_to_tw(gcal_item)
        diff_keys = {k for k in set(tw_item) ^ set(tw_item_out)}
        changes = {
            k: (tw_item[k], tw_item_out[k])
            for k in set(tw_item) & set(tw_item_out)
            if tw_item[k] != tw_item_out[k]
        }

        return diff_keys, changes

    @staticmethod
    def convert_tw_to_gcal(tw_item: dict) -> dict:
        """Convert a TW item to a Gcal event.

        .. note:: Do not convert the ID as that may change either manually or
                  after marking the task as "DONE"
        """

        assert all(
            [i in tw_item.keys() for i in ["description", "status", "uuid"]]
        ), "Missing keys in tw_item"

        gcal_item = {}

        # Summary
        gcal_item["summary"] = tw_item["description"]

        # description
        gcal_item["description"] = "IMPORTED FROM TASKWARRIOR\n"
        if "annotations" in tw_item.keys():
            for i, a in enumerate(tw_item["annotations"]):
                gcal_item["description"] += f"\n* Annotation {i + 1}: {a}"

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

    @staticmethod
    def convert_gcal_to_tw(gcal_item: dict) -> dict:
        """Convert a GCal event to a TW item."""

        # Parse the description
        annotations, status, uuid = TWGCalAggregator._parse_gcal_item_desc(gcal_item)
        assert isinstance(annotations, list)
        assert isinstance(status, str)
        assert isinstance(uuid, UUID) or uuid is None

        tw_item: Dict[str, Any] = {}
        # annotations
        tw_item["annotations"] = annotations

        # alias - make aliases dict?
        if status == "done":
            status = "completed"

        # Status
        if status not in ["pending", "completed", "deleted", "waiting", "recurring"]:
            logger.warning(
                "Invalid status %s in GCal->TW conversion of item. Skipping status:" % status
            )
        else:
            tw_item["status"] = status

        # uuid - may just be created -, thus not there
        if uuid is not None:
            tw_item["uuid"] = uuid

        # Description
        tw_item["description"] = gcal_item["summary"]

        # don't meddle with the 'entry' field
        tw_item["due"] = GCalSide.get_event_time(gcal_item, t="end")

        # update time
        if "updated" in gcal_item.keys():
            tw_item["modified"] = GCalSide.parse_datetime(gcal_item["updated"])

        # Note:
        # Don't add extra fields of GCal as TW annotations 'cause then, if
        # converted backwards, these annotations are going in the description of
        # the Gcal event and then these are going into the event description and
        # this happens on every conversion. Add them as new TW UDAs if needed

        # add annotation
        return tw_item

    @staticmethod
    def _parse_gcal_item_desc(gcal_item: dict) -> Tuple[List[str], str, Union[UUID, None]]:
        """Parse and return the necessary TW fields off a Google Calendar Item."""
        annotations: List[str] = []
        status = "pending"
        uuid = None

        if "description" not in gcal_item.keys():
            return annotations, status, uuid

        gcal_desc = gcal_item["description"]
        # strip whitespaces, empty lines
        lines = [l.strip() for l in gcal_desc.split("\n") if l][1:]

        # annotations
        i = 0
        for i, l in enumerate(lines):
            parts = l.split(":", maxsplit=1)
            if len(parts) == 2 and parts[0].lower().startswith("* annotation"):
                annotations.append(parts[1].strip())
            else:
                break

        if i == len(lines) - 1:
            return annotations, status, uuid

        # Iterate through rest of lines, find only the status and uuid ones
        for l in lines[i:]:
            parts = l.split(":", maxsplit=1)
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
