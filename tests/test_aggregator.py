from typing import Optional, Sequence

from item_synchronizer.types import ID

from syncall.sync_side import ItemType, SyncSide


class MockSide(SyncSide):
    def __init__(self, name: str, fullname: str, *args, **kargs) -> None:
        self._fullname = fullname
        self._name = name

    def __str__(self) -> str:
        return self._fullname

    def get_all_items(self, **kargs) -> Sequence[ItemType]:
        raise NotImplementedError("Implement in derived")

    def get_item(self, item_id: ID, use_cached: bool = False) -> Optional[ItemType]:
        raise NotImplementedError("Should be implemented in derived")

    def delete_single_item(self, item_id: ID):
        raise NotImplementedError("Should be implemented in derived")

    def update_item(self, item_id: ID, **changes):
        raise NotImplementedError("Should be implemented in derived")

    def add_item(self, item: ItemType) -> ItemType:
        raise NotImplementedError("Implement in derived")

    @classmethod
    def id_key(cls) -> str:
        raise NotImplementedError("Implement in derived")

    @classmethod
    def summary_key(cls) -> str:
        raise NotImplementedError("Implement in derived")

    @classmethod
    def items_are_identical(
        cls, item1: ItemType, item2: ItemType, ignore_keys: Sequence[str] = []
    ) -> bool:
        """Determine whether two items are identical.

        .. returns:: True if items are identical, False otherwise.
        """
        raise NotImplementedError("Implement in derived")
