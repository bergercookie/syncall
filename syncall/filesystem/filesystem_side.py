from pathlib import Path
from typing import MutableMapping, Optional, Sequence

from item_synchronizer.types import ID
from loguru import logger

from syncall.concrete_item import ConcreteItem
from syncall.filesystem.filesystem_file import FilesystemFile
from syncall.sync_side import SyncSide


class FilesystemSide(SyncSide):
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

    def __init__(self, filesystem_root: Path, filename_extension: str) -> None:
        super().__init__(name="Fs", fullname="Filesystem")
        self._filesystem_root = filesystem_root

        if not filename_extension.startswith("."):
            filename_extension = f".{filename_extension}"

        self._filename_extension = filename_extension

        all_items = self.get_all_items()
        self._items_cache: MutableMapping[ID, FilesystemFile] = {
            item.id: item for item in all_items
        }

    @property
    def filesystem_root(self) -> Path:
        return self._filesystem_root

    def start(self):
        pass

    def finish(self):
        for item in self._items_cache.values():
            item.flush()

    def get_all_items(self, **kargs) -> Sequence[FilesystemFile]:
        """Read all items again from storage."""
        all_items = tuple(
            FilesystemFile(path=p)
            for p in self._filesystem_root.iterdir()
            if p.is_file() and p.suffix == self._filename_extension
        )

        logger.opt(lazy=True).debug(
            f"Found {len(all_items)} matching files under {self._filesystem_root} using"
            f" extension {self._filename_extension}"
        )

        return all_items

    def get_item(self, item_id: ID, use_cached: bool = False) -> Optional[FilesystemFile]:
        item = self._items_cache.get(item_id)
        if not use_cached or item is None:
            logger.trace(f"Couldn't find item {item_id} in cache, fetching from filesystem...")
            item = self._get_item_refresh(item_id=item_id)

        return item

    def _get_item_refresh(self, item_id: ID) -> Optional[FilesystemFile]:
        """Search for the FilesystemFile in the root directory given its ID."""
        fs_files = [FilesystemFile(path) for path in self._filesystem_root.iterdir()]

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
