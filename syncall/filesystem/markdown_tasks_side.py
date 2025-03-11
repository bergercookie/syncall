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

        self.all_items = self.get_all_items()
        self._items_cache: dict[str, dict] = {
            item.id: item for item in self.get_all_items()
        }

    def start(self):
        pass

    def finish(self):
        self._filesystem_file.flush()

    def get_all_items(self, **kargs) -> Sequence[FilesystemFile]:
        """Read all items again from storage."""
        all_items = tuple(
            MarkdownTaskItem(
                is_checked=True,
                last_modified_date=True,
                title=line,
            )
            for line in self._filesystem_file.contents
            if line.startswith("- [")
        )

        logger.opt(lazy=True).debug(
            f"Found {len(all_items)} matching tasks inside {self._filename_path}"
        )
        return all_items

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

        item.title = changes["title"]
        item.is_checked = changes["is_checked"]

    def add_item(self, item: MarkdownTaskItem) -> FilesystemFile:
        item = MarkdownTaskItem.from_raw_item(item)
        self._items_cache[item.id] = item
        return item

    @classmethod
    def items_are_identical(
        cls, item1: ConcreteItem, item2: ConcreteItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = [cls.last_modification_key()]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)
