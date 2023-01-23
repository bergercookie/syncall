from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from bidict import bidict  # type: ignore
from bubop import PrefsManager, logger, pickle_dump, pickle_load
from item_synchronizer import Synchronizer
from item_synchronizer.helpers import SideChanges
from item_synchronizer.resolution_strategy import AlwaysSecondRS, ResolutionStrategy
from item_synchronizer.types import ID, ConverterFn, Item

from syncall.app_utils import app_name
from syncall.side_helper import SideHelper
from syncall.sync_side import SyncSide


class Aggregator:
    """Aggregator class that manages the synchronization between two arbitrary sides.

    Having an aggregator is handy for managing push/pull/sync directives in a
    consistent manner.
    """

    def __init__(
        self,
        *,
        side_A: SyncSide,
        side_B: SyncSide,
        converter_B_to_A: ConverterFn,
        converter_A_to_B: ConverterFn,
        resolution_strategy: ResolutionStrategy = AlwaysSecondRS(),
        config_fname: Optional[str] = None,
        ignore_keys: Tuple[Sequence[str], Sequence[str]] = tuple(),
    ):
        # Preferences manager
        # Sample config path: ~/.config/syncall/taskwarrior_gcal_sync.yaml
        #                     ~/.config/syncall/taskwarrior_notion_sync.yaml
        #
        # The stem of the filename can be overridden by the user if they provide `config_fname`.
        #
        # Serdes dirs are shared across multiple different syncrhonizers
        # Sample serdes dirs: ~/.config/syncall/serdes/gcal/
        #                     ~/.config/syncall/serdes/tw/
        if config_fname is None:
            config_fname = f"{side_B.name}_{side_A.name}_sync".lower()
        else:
            logger.debug(f"Using a custom configuration file ... -> {config_fname}")

        self.prefs_manager = PrefsManager(app_name=app_name(), config_fname=config_fname)

        # Own config
        self.config: Dict[str, Any] = {}

        self._side_A: SyncSide = side_A
        self._side_B: SyncSide = side_B

        # Initialize helpers - one for each side ----------------------------------------------
        self._helper_A = SideHelper.from_side(self._side_A)
        self._helper_B = SideHelper.from_side(self._side_B)
        self._helper_A.other = self._helper_B
        self._helper_B.other = self._helper_A

        # ignore keys
        if ignore_keys:
            self._helper_A.ignore_keys = ignore_keys[0]
            self._helper_B.ignore_keys = ignore_keys[1]

        # serdes directories for storing cached versions of items for each side ---------------
        self.serdes_dirs = self.prefs_manager.config_directory / "serdes"
        serdes_A = self.serdes_dirs / self._side_A.name.lower()
        serdes_B = self.serdes_dirs / self._side_B.name.lower()
        serdes_A.mkdir(exist_ok=True, parents=True)
        serdes_B.mkdir(exist_ok=True)

        self.config[f"{self._helper_A}_serdes"] = serdes_A
        self.config[f"{self._helper_B}_serdes"] = serdes_B

        # Correspondences between the two sides -----------------------------------------------
        # For finding the matches between IDs of the two sides
        # e.g., for Taskwarrior <-> Gcal: tw_gcal_ids
        correspondences_prefs_key = f"{self._side_B.name}_{self._side_A.name}_ids"
        if correspondences_prefs_key not in self.prefs_manager:
            self.prefs_manager[correspondences_prefs_key] = bidict()
        self._B_to_A_map: bidict = self.prefs_manager[correspondences_prefs_key]

        # resolution strategy to resolve conflicts
        self._resolution_strategy = resolution_strategy

        # item synchronizer -------------------------------------------------------------------
        def side_B_fn(fn):
            wrapped = partial(fn, helper=self._helper_B)
            wrapped.__doc__ = f"{self._helper_B} {fn.__doc__}"
            return wrapped

        def side_A_fn(fn):
            wrapped = partial(fn, helper=self._helper_A)
            wrapped.__doc__ = f"{self._helper_A} {fn.__doc__}"
            return wrapped

        self._synchronizer = Synchronizer(
            A_to_B=self._B_to_A_map.inverse,
            inserter_to_A=side_A_fn(self.inserter_to),
            inserter_to_B=side_B_fn(self.inserter_to),
            updater_to_A=side_A_fn(self.updater_to),
            updater_to_B=side_B_fn(self.updater_to),
            deleter_to_A=side_A_fn(self.deleter_to),
            deleter_to_B=side_B_fn(self.deleter_to),
            converter_to_A=converter_B_to_A,
            converter_to_B=converter_A_to_B,
            item_getter_A=side_A_fn(self.item_getter_for),
            item_getter_B=side_B_fn(self.item_getter_for),
            resolution_strategy=self._resolution_strategy,
            side_names=(side_A.fullname, side_B.fullname),
        )

        self.cleaned_up = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.finish()

    def detect_changes(self, helper: SideHelper, items: Dict[ID, Item]) -> SideChanges:
        """
        Given a fresh list of items from the SyncSide, determine which of them are new,
        modified, or have been deleted since the last run.
        """
        serdes_dir, _ = self._get_serdes_dirs(helper)
        logger.info(f"Detecting changes from {helper}...")
        item_ids = set(items.keys())
        # New items exist in the sync side but don't yet exist in my IDs correspndences.
        new = {
            item_id for item_id in item_ids if item_id not in self._get_ids_map(helper=helper)
        }
        # Deleted items do not exist in the sync side but still yet exist in my IDs
        # correspndences.
        #
        # Exclude the already new ones determined in the earlier step
        deleted = {
            registered_id
            for registered_id in self._get_ids_map(helper=helper)
            if registered_id not in item_ids.difference(new)
        }

        # Potentially modified items are all the items that exist in the sync side minus the
        # ones already determined as deleted or new
        #
        # For these items, load the cached version and check whether they are the same or not
        # to actually determine the ones that are changed.
        modified = set()
        potentially_modified_ids = item_ids.difference(new.union(deleted))
        for item_id in potentially_modified_ids:
            item = items[item_id]
            cached_item = pickle_load(serdes_dir / item_id)
            if self._item_has_update(prev_item=cached_item, new_item=item, helper=helper):
                modified.add(item_id)

        side_changes = SideChanges(new=new, modified=modified, deleted=deleted)
        logger.debug(f"\n\n{side_changes}")

        return side_changes

    def sync(self):
        """Entrypoint method."""
        items_A = {
            str(item[self._helper_A.id_key]): item for item in self._side_A.get_all_items()
        }
        items_B = {
            str(item[self._helper_B.id_key]): item for item in self._side_B.get_all_items()
        }

        # find what's changed in each side
        changes_A = self.detect_changes(self._helper_A, items_A)
        changes_B = self.detect_changes(self._helper_B, items_B)

        # pickle items that are new or updated
        side_A_serdes_dir, side_B_serdes_dir = self._get_serdes_dirs(self._helper_A)
        side_A, side_B = self._get_side_instances(self._helper_A)
        for item_id in changes_B.new.union(changes_B.modified):
            item = side_B.get_item(item_id)
            if item is None:
                raise RuntimeError(f"Failed to retrieve serialized version of Item {item_id}")
            pickle_dump(item, side_B_serdes_dir / item_id)
        for item_id in changes_A.new.union(changes_A.modified):
            item = side_A.get_item(item_id)
            if item is None:
                raise RuntimeError(f"Failed to retrieve serialized version of Item {item_id}")
            pickle_dump(item, side_A_serdes_dir / item_id)

        # remove deleted pickled items
        self._remove_serdes_files(helper=self._helper_B, ids=changes_B.deleted)
        self._remove_serdes_files(helper=self._helper_A, ids=changes_A.deleted)

        # synchronize
        self._synchronizer.sync(changes_A=changes_A, changes_B=changes_B)

    def start(self):
        """Initialization actions."""
        self._side_A.start()
        self._side_B.start()

    def finish(self):
        """Finalization actions."""
        self._side_A.finish()
        self._side_B.finish()

    # InserterFn = Callable[[Item], ID]
    def inserter_to(self, item: Item, helper: SideHelper) -> ID:
        """Inserter.

        Other side already has the item, and I'm also inserting it at this side.
        """
        item_side, _ = self._get_side_instances(helper)
        serdes_dir, _ = self._get_serdes_dirs(helper)
        logger.info(
            f"[{helper.other}] Inserting item [{self._summary_of(item, helper):10}] at"
            f" {helper}..."
        )

        item_created = item_side.add_item(item)
        item_created_id = str(item_created[helper.id_key])

        # Cache both sides with pickle - f=id_
        logger.debug(f'Pickling newly created {helper} item -> "{item_created_id}"')
        pickle_dump(item_created, serdes_dir / item_created_id)

        return item_created_id

    def updater_to(self, item_id: ID, item: Item, helper: SideHelper):
        """Updater."""
        side, _ = self._get_side_instances(helper)
        serdes_dir, _ = self._get_serdes_dirs(helper)
        logger.info(
            f"[{helper.other}] Updating item [{self._summary_of(item, helper):10}] at"
            f" {helper}..."
        )

        side.update_item(item_id, **item)
        pickle_dump(item, serdes_dir / item_id)

    def deleter_to(self, item_id: ID, helper: SideHelper):
        """Deleter."""
        logger.info(f"[{helper}] Synchronising deleted item, id -> {item_id}...")
        side, _ = self._get_side_instances(helper)
        side.delete_single_item(item_id)

        self._remove_serdes_files(helper=helper, ids=(item_id,))

    def item_getter_for(self, item_id: ID, helper: SideHelper) -> Item:
        """Item Getter."""
        logger.debug(f"Fetching {helper} item for id -> {item_id}")
        side, _ = self._get_side_instances(helper)
        item = side.get_item(item_id)
        return item

    def _item_has_update(self, prev_item: Item, new_item: Item, helper: SideHelper) -> bool:
        """Determine whether the item has been updated."""
        side, _ = self._get_side_instances(helper)

        return not side.items_are_identical(
            prev_item, new_item, ignore_keys=[helper.id_key, *helper.ignore_keys]
        )

    def _get_ids_map(self, helper: SideHelper):
        return self._B_to_A_map if helper is self._helper_B else self._B_to_A_map.inverse

    def _get_serdes_dirs(self, helper: SideHelper) -> Tuple[Path, Path]:
        serdes_dir = self.config[f"{helper}_serdes"]
        other_serdes_dir = self.config[f"{helper.other}_serdes"]

        return serdes_dir, other_serdes_dir

    def _get_side_instances(self, helper: SideHelper) -> Tuple[SyncSide, SyncSide]:
        side = self._side_B if helper is self._helper_B else self._side_A
        other_side = self._side_A if helper is self._helper_B else self._side_B

        return side, other_side

    def _remove_serdes_files(self, helper: SideHelper, *, ids: Iterable[ID]):
        serdes_dir, _ = self._get_serdes_dirs(helper)

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

    def _summary_of(self, item: Item, helper: SideHelper, short=True) -> str:
        """Get the summary of the given item."""
        ret = item[helper.summary_key]
        if short:
            return ret[:10]

        return ret
