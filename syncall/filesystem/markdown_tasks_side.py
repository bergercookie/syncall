from pathlib import Path
from typing import MutableMapping, Optional, Sequence

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

    def __init__(self, filename_path: Path) -> None:
        super().__init__(name="Fs", fullname="Filesystem")
        self._filename_path = filename_path
        self._filesystem_file = FilesystemFile(path=filename_path)

        all_items = self.get_all_items()

    def start(self):
        pass

    def finish(self):
        self._filesystem_file.flush()

    def get_all_items(self, **kargs) -> Sequence[FilesystemFile]:
        """Read all items again from storage."""
        all_items = tuple(
            MarkdownTask(line)
            for line in self._filesystem_file.contents
            if line.startswith("- [")
        )

        logger.opt(lazy=True).debug(
            f"Found {len(all_items)} matching tasks inside {self._filename_path}"
        )

        return all_items

    def get_item(self, item_id: ID) -> Optional[MarkdownTasksSide]:
        item = self._get_item_refresh(item_id=item_id)

        return item

    def _get_item_refresh(self, item_id: ID) -> Optional[FilesystemFile]:
        """Search for the FilesystemFile in the root directory given its ID."""
        fs_files = self.get_all_items()

        matching_fs_files = [fs_file for fs_file in fs_files if fs_file.id == item_id]
        if len(matching_fs_files) > 1:
            logger.warning(
                f"Found {len(matching_fs_files)} paths with the item ID [{item_id}]."
                "Arbitrarily returning the first item."
            )
        elif len(matching_fs_files) == 0:
            return None

        # update the cache & return
        item = matching_fs_files[0]
        self._items_cache[item_id] = item
        return item

    def delete_single_item(self, item_id: ID):
        item = self.get_item(item_id)
        if item is None:
            logger.warning(f"Requested to delete item {item_id} but item cannot be found.")
            return

        item.delete()
        item.flush()

    def update_item(self, item_id: ID, **changes):
        item = self.get_item(item_id)
        if item is None:
            logger.warning(f"Requested to update item {item_id} but item cannot be found.")
            return

        if not {"title", "contents"}.issubset(changes):
            logger.warning(f"Invalid changes provided to Fielsystem Side -> {changes}")
            return

        item.title = changes["title"]
        item.contents = changes["contents"]
        item.flush()

    def add_item(self, item: FilesystemFile) -> FilesystemFile:
        item.root = self.filesystem_root
        item.flush()
        return item

    @classmethod
    def items_are_identical(
        cls, item1: ConcreteItem, item2: ConcreteItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = [cls.last_modification_key()]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)
