import datetime
import pickle
import re

from pathlib import Path
from typing import MutableMapping, Optional, Sequence, cast

from item_synchronizer.types import ID
from loguru import logger

from syncall.concrete_item import ConcreteItem
from syncall.filesystem.filesystem_file import FilesystemFile
from syncall.filesystem.markdown_task_item import MarkdownTaskItem
from syncall.sync_side import SyncSide


class MarkdownTasksSide(SyncSide):
    """Integration for managing files in a local filesystem.

    - Embed the UUID as an extended attribute of each file.
    """

    @classmethod
    def id_key(cls) -> str:
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        return "title"

    @classmethod
    def last_modification_key(cls) -> str:
        return "last_modified_date"

    def __init__(self, markdown_file: Path) -> None:
        super().__init__(name="Fs", fullname="Filesystem")
        self._filename_path = markdown_file
        self._filesystem_file = FilesystemFile(path=markdown_file)
        self._filesystem_ids_path = Path(f".{markdown_file}.ids")

        self._ids_map = {}
        if self._filesystem_ids_path.is_file():
            with self._filesystem_ids_path.open("rb") as f:
                self._ids_map = pickle.load(f)

        all_items = self.get_all_items(include_non_tasks=True)

        # dict with items. Ignore lines with no tasks
        self._items_cache: dict[str, dict] = {
            str(item.id): item for item in all_items if item
        }

        # Array with item ids in the same order found in the .md file
        # It will have None in positions with no Markdown tasks
        self._items_order = [ str(item.id) if item else None for item in all_items ]

    def start(self):
        pass

    def finish(self):
        contents = ""
        # add existing file lines as they are if they are not tasks
        # or change them for the tasks in text format when appropriate
        for item_id, line in zip(self._items_order, self._filesystem_file.contents.splitlines()):
            if item_id:
                try:
                    line_content = str(self.get_item(item_id))
                except KeyError:
                    continue
            else:
                line_content = line

            contents += line_content + "\n"

        # so far we've inserted older tasks. add newly synced ones
        new_ids = [ item_id for item_id in self._items_cache.keys() if item_id not in self._items_order ]
        for item_id in new_ids:
            line_content = str(self.get_item(item_id))
            contents += line_content + "\n"

        self._filesystem_file.contents = contents
        self._filesystem_file.flush()

        # delete id mappings if the item no longer exist
        existing_ids = [ str(item._id()) for item in self._items_cache.values() ]
        self._ids_map = {new_id: persistent_id for new_id, persistent_id in self._ids_map.items() if new_id in existing_ids}

        with self._filesystem_ids_path.open("wb") as f:
            pickle.dump(self._ids_map, f)

    def get_persistent_id(self, id):
    # Markdown doesnt keep a stable id as it's just a text format
    # We record ids in a pickle file if they change
    # so the map in Syncronizer works as expected
    # this would be the first id ever set for an item
        try:
            return self._ids_map[str(id)]
        except KeyError:
            return id

    def get_all_items(self, **kargs) -> Sequence[FilesystemFile]:
        """Read all items again from storage."""
        """The array will have None in lines with no tasks"""
        result = []
        found_tasks = 0
        for line in self._filesystem_file.contents.splitlines():
            item = MarkdownTaskItem.from_markdown(line, self._filesystem_file)
            if item:
                found_tasks += 1
                item_id = item._id()
                persistent_id = self.get_persistent_id(item_id)
                if persistent_id != item_id:
                    item._persistent_id = persistent_id
            if item or kargs.get('include_non_tasks'):
                result.append(item)

        logger.opt(lazy=True).debug(
            f"Found {found_tasks} matching tasks inside {self._filename_path}"
        )
        return result

    def get_item(self, item_id: ID) -> Optional[MarkdownTaskItem]:
        item = self._items_cache.get(item_id)
        return item

    def delete_single_item(self, item_id: ID):
        try:
            del self._items_cache[item_id]
        except Keyerror:
            logger.warning(f"Requested to delete item {item_id} but item cannot be found.")
            return

    def update_item(self, item_id: ID, **changes):
        item = self.get_item(item_id)
        if item is None:
            logger.warning(f"Requested to update item {item_id} but item cannot be found.")
            return

        if not {"title", "is_checked"}.issubset(changes):
            logger.warning(f"Invalid changes provided to Filesystem Side -> {changes}")
            return

        if item.title != changes["title"]:
            item.title = changes["title"]
            logger.warning(f"The item {item_id} has changed its id to {item._id()}")
            self._ids_map[str(item._id())] = item_id

        item.is_checked = changes["is_checked"]

    def add_item(self, item: MarkdownTaskItem) -> FilesystemFile:
        item = MarkdownTaskItem.from_raw_item(item)
        self._items_cache[item.id] = item
        return item

    @classmethod
    def items_are_identical(
        cls, item1: ConcreteItem, item2: ConcreteItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        # item1 = item1.copy()
        # item2 = item2.copy()

        keys = [
            k
            for k in [
                "id",
                "title",
                "is_checked",
                "due_date",
                "done_date",
            ]
            if k not in ignore_keys
        ]
        return SyncSide._items_are_identical(item1, item2, keys)
