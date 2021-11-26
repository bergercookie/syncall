from __future__ import annotations

import pickle
import traceback
from datetime import datetime, timedelta
from enum import Enum
from functools import cached_property, partial
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from uuid import UUID

from bidict import bidict  # type: ignore
from item_synchronizer import Synchronizer
from item_synchronizer.helpers import SideChanges
from item_synchronizer.resolution_strategy import AlwaysSecondRS
from item_synchronizer.types import ID, Item
from loguru import logger

from taskw_gcal_sync import GCalSide, GenericSide, TaskWarriorSide
from taskw_gcal_sync.PrefsManager import PrefsManager


def pickle_dump(item: Dict[str, Any], path: Union[Path, str], *args, **kargs):
    pickle.dump(item, Path(path).open("wb"), *args, **kargs, protocol=0)


def pickle_load(path: Union[Path, str]):
    return pickle.load(Path(path).open("rb"))


class ItemEnum(Enum):
    GCAL = "GCAL"
    TW = "TW"

    @cached_property
    def other(self) -> ItemEnum:
        return _item_type_to_other[self]

    @cached_property
    def id_key(self) -> str:
        return str(_item_type_to_id_key[self])

    def __str__(self):
        return str(self.value)


_item_type_to_other = {
    ItemEnum.TW: ItemEnum.GCAL,
    ItemEnum.GCAL: ItemEnum.TW,
}

_item_type_to_id_key = {
    ItemEnum.TW: "uuid",
    ItemEnum.GCAL: "id",
}


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

        self.config[f"{ItemEnum.TW}_serdes_dir"] = (
            Path(self.prefs_manager.prefs_dir_full) / "pickle_tw"
        )
        self.config[f"{ItemEnum.GCAL}_serdes_dir"] = (
            Path(self.prefs_manager.prefs_dir_full) / "pickle_gcal"
        )
        self.config.update(**kargs)  # Update

        # initialise both sides ---------------------------------------------------------------
        # taskwarrior
        tw_config_new = {}
        tw_config_new.update(tw_config)
        self._tw_side = TaskWarriorSide(**tw_config_new)

        # gcal
        gcal_config_new = {}
        gcal_config_new.update(gcal_config)
        self._gcal_side = GCalSide(**gcal_config_new)  # type: ignore

        # Correspondences between the TW reminders and the GCal events ------------------------
        # For finding the matches: [TW] uuid <-> [GCal] id
        if "tw_gcal_ids" not in self.prefs_manager:
            self.prefs_manager["tw_gcal_ids"] = bidict()
        self._tw_gcal_ids: bidict = self.prefs_manager["tw_gcal_ids"]
        self._resolution_strategy = AlwaysSecondRS()

        # item synchronizer -------------------------------------------------------------------
        # A = GCal
        # B = TW

        def taskw_fn(fn):
            wrapped = partial(fn, item_enum=ItemEnum.TW)
            wrapped.__doc__ = f"{ItemEnum.TW} {fn.__doc__}"
            return wrapped

        def gcal_fn(fn):
            wrapped = partial(fn, item_enum=ItemEnum.GCAL)
            wrapped.__doc__ = f"{ItemEnum.GCAL} {fn.__doc__}"
            return wrapped

        self._synchronizer = Synchronizer(
            A_to_B=self._tw_gcal_ids.inverse,
            inserter_to_A=gcal_fn(self.inserter_to),  # type: ignore
            inserter_to_B=taskw_fn(self.inserter_to),  # type: ignore
            updater_to_A=gcal_fn(self.updater_to),
            updater_to_B=taskw_fn(self.updater_to),
            deleter_to_A=gcal_fn(self.deleter_to),
            deleter_to_B=taskw_fn(self.deleter_to),
            converter_to_A=TWGCalAggregator.convert_tw_to_gcal,
            converter_to_B=TWGCalAggregator.convert_gcal_to_tw,
            item_getter_A=gcal_fn(self.item_getter_for),
            item_getter_B=taskw_fn(self.item_getter_for),
            resolution_strategy=self._resolution_strategy,
            side_names=("Google Calendar", "Taskwarrior"),
        )

        self.cleaned_up = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        pass

    def detect_changes(self, item_enum: ItemEnum, items: Dict[ID, Item]) -> SideChanges:
        serdes_dir, _ = self._get_serdes_dirs(item_enum)
        logger.info(f"Detecting changes from {item_enum}...")
        item_ids = set(items.keys())
        new = {
            item_id
            for item_id in item_ids
            if item_id not in self._get_registered_ids(item_enum=item_enum)
        }
        deleted = {
            registered_id
            for registered_id in self._get_registered_ids(item_enum=item_enum)
            if registered_id not in item_ids.difference(new)
        }

        modified = set()
        potentially_modified_ids = item_ids.difference(new.union(deleted))
        for item_id in potentially_modified_ids:
            item = items[item_id]
            cached_item = pickle_load(serdes_dir / item_id)
            if self._item_has_update(
                prev_item=cached_item, new_item=item, item_enum=item_enum
            ):
                modified.add(item_id)

        side_changes = SideChanges(new=new, modified=modified, deleted=deleted)
        logger.debug(f"\n\n{side_changes}")

        return side_changes

    def sync(self):
        """Entrypoint method."""
        tw_items = {
            str(item[ItemEnum.TW.id_key]): item for item in self._tw_side.get_all_items()
        }
        gcal_items = {
            str(item[ItemEnum.GCAL.id_key]): item for item in self._gcal_side.get_all_items()
        }

        # find what's changed in each side
        gcal_changes = self.detect_changes(ItemEnum.GCAL, gcal_items)
        tw_changes = self.detect_changes(ItemEnum.TW, tw_items)

        # pickle items that are new or updated
        tw_serdes_dir, gcal_serdes_dir = self._get_serdes_dirs(ItemEnum.TW)
        tw_side, gcal_side = self._get_side_instances(ItemEnum.TW)
        for item_id in tw_changes.new.union(tw_changes.modified):
            item = tw_side.get_item(item_id)
            if item is None:
                raise RuntimeError
            pickle_dump(item, tw_serdes_dir / item_id)
        for item_id in gcal_changes.new.union(gcal_changes.modified):
            item = gcal_side.get_item(item_id)
            if item is None:
                raise RuntimeError
            pickle_dump(item, gcal_serdes_dir / item_id)

        # remove deleted pickled items
        self._remove_serdes_files(item_enum=ItemEnum.TW, ids=tw_changes.deleted)
        self._remove_serdes_files(item_enum=ItemEnum.GCAL, ids=gcal_changes.deleted)

        # synchronise
        self._synchronizer.sync(changes_A=gcal_changes, changes_B=tw_changes)

    def start(self):
        self._tw_side.start()
        self._gcal_side.start()

        self.config[f"{ItemEnum.TW}_serdes_dir"].mkdir(exist_ok=True)
        self.config[f"{ItemEnum.GCAL}_serdes_dir"].mkdir(exist_ok=True)

    # InserterFn = Callable[[Item], ID]
    def inserter_to(self, item: Item, item_enum: ItemEnum) -> ID:
        """Inserter.

        Other side already has the item, and I'm also inserting it at this side."""
        item_side, _ = self._get_side_instances(item_enum)
        serdes_dir, _ = self._get_serdes_dirs(item_enum)
        logger.info(
            f"[{item_enum.other}] Inserting item [{self._summary_of(item, item_enum):10}] at"
            f" {item_enum}..."
        )

        item_created = item_side.add_item(item)
        item_created_id = str(item_created[item_enum.id_key])

        # Cache both sides with pickle - f=id_
        logger.debug(f'Pickling newly created {item_enum} item -> "{item_created_id}"')
        pickle_dump(item, serdes_dir / item_created_id)

        return item_created_id

    def updater_to(self, item_id: ID, item: Item, item_enum: ItemEnum):
        """Updater."""
        side, _ = self._get_side_instances(item_enum)
        serdes_dir, _ = self._get_serdes_dirs(item_enum)
        logger.info(
            f"[{item_enum.other}] Updating item [{self._summary_of(item, item_enum):10}] at"
            f" {item_enum}..."
        )

        side.update_item(item_id, **item)
        pickle_dump(item, serdes_dir / item_id)

    def deleter_to(self, item_id: ID, item_enum: ItemEnum):
        """Deleter."""
        logger.info(f"[{item_enum}] Synchronising deleted item, id -> {item_id}...")
        side, _ = self._get_side_instances(item_enum)
        serdes_dir, _ = self._get_serdes_dirs(item_enum)
        side.delete_single_item(item_id)

        self._remove_serdes_files(item_enum=item_enum, ids=(item_id,))

    def item_getter_for(self, item_id: ID, item_enum: ItemEnum) -> Item:
        """Item Getter."""
        logger.debug(f"Fetching {item_enum} item for id -> {item_id}")
        side, _ = self._get_side_instances(item_enum)
        item = side.get_item(item_id)
        return item

    def _item_has_update(self, prev_item: Item, new_item: Item, item_enum: ItemEnum) -> bool:
        """Determine whether the item has been updated."""
        side, _ = self._get_side_instances(item_enum)
        return not side.items_are_identical(
            prev_item, new_item, ignore_keys=["urgency", "modified", "updated"]
        )

    def _get_registered_ids(self, item_enum: ItemEnum):
        return self._tw_gcal_ids if item_enum is ItemEnum.TW else self._tw_gcal_ids.inverse

    def _get_serdes_dirs(self, item_enum: ItemEnum) -> Tuple[Path, Path]:
        serdes_dir = self.config[f"{item_enum}_serdes_dir"]
        other_serdes_dir = self.config[f"{item_enum.other}_serdes_dir"]

        return serdes_dir, other_serdes_dir

    def _get_side_instances(self, item_enum: ItemEnum) -> Tuple[GenericSide, GenericSide]:
        side = self._tw_side if item_enum is ItemEnum.TW else self._gcal_side
        other_side = self._gcal_side if item_enum is ItemEnum.TW else self._tw_side

        return side, other_side

    def _remove_serdes_files(self, item_enum: ItemEnum, *, ids: Iterable[ID]):
        serdes_dir, _ = self._get_serdes_dirs(item_enum)

        def full_path(id_: ID) -> Path:
            return serdes_dir / str(id_)

        for id_ in ids:
            p = full_path(id_)
            try:
                p.unlink()
            except FileNotFoundError:
                logger.warning(f"File doesn't exist, this may indicate an error -> {p}")
                logger.opt(exception=True).debug(
                    f"File doesn't exist, this may indicate an error -> {p}"
                )

    def _summary_of(self, item: Item, item_enum: ItemEnum, short=True) -> str:
        """Get the summary of the given item."""
        if item_enum == ItemEnum.TW:
            key = "description"
        else:
            key = "summary"

        ret = item[key]
        if short:
            return ret[:10]

        return ret

    @staticmethod
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

    @staticmethod
    def convert_gcal_to_tw(gcal_item: Item) -> Item:
        """GCal -> TW Converter."""

        # Parse the description
        annotations, status, uuid = TWGCalAggregator._parse_gcal_item_desc(gcal_item)
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
            logger.warning(
                "Invalid status {status} in GCal->TW conversion of item. Skipping status:"
            )
        else:
            tw_item["status"] = status

        # uuid - may just be created -, thus not there
        if uuid is not None:
            tw_item["uuid"] = uuid

        # Description
        tw_item["description"] = gcal_item["summary"]

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

        # TODO add annotation
        return tw_item

    @staticmethod
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
