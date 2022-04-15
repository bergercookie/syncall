import abc
import datetime
from typing import Any, Mapping, Optional, Sequence, final

from bubop.time import is_same_datetime
from item_synchronizer.types import ID
from loguru import logger

ItemType = Mapping[str, Any]


class SyncSide(abc.ABC):
    """Interface class for interacting with the various synchronization sides.

    Sets the public common methods that all synchronization classes should have.

    .. todo:: This is not used directly by the Synchronizer and is part of this repo mainly
    because it fits the common theme and could be handy for modules implementing the classes of
    item_synchronizer.
    """

    def __init__(self, name: str, fullname: str, *args, **kargs) -> None:
        self._fullname = fullname
        self._name = name

    def __str__(self) -> str:
        return self._fullname

    @final
    @property
    def fullname(self) -> str:
        return self._fullname

    @final
    @property
    def name(self) -> str:
        return self._name

    def start(self):
        """Initialization steps.

        Call this manually. Derived classes can take care of setting up data
        structures / connection, authentication requests etc.
        """
        pass

    def finish(self):
        """Finalization steps.

        Call this manually. Derived classes can take care of closing open connections, flashing
        their cached data, etc.
        """
        pass

    @abc.abstractmethod
    def get_all_items(self, **kargs) -> Sequence[ItemType]:
        """Query side and return a sequence of items

        :param kargs: Extra options for the call
        :return: A list of items. The type of these items depends on the derived class
        """
        raise NotImplementedError("Implement in derived")

    @abc.abstractmethod
    def get_item(self, item_id: ID, use_cached: bool = False) -> Optional[ItemType]:
        """Get a single item based on the given UUID.

        :use_cached: False if you want to fetch the latest version of the item. True if a
                     cached version would do.
        :returns: None if not found, the item in dict representation otherwise
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def delete_single_item(self, item_id: ID):
        """Delete an item based on the given UUID.

        .. raises:: Keyerror if item is not found.
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def update_item(self, item_id: ID, **changes):
        """Update with the given item.

        :param item_id : ID of item to update
        :param changes: Keyword only parameters that are to change in the item
        .. warning:: The item must already be present
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def add_item(self, item: ItemType) -> ItemType:
        """Add a new item.

        :returns: The newly added event
        """
        raise NotImplementedError("Implement in derived")

    @classmethod
    @abc.abstractmethod
    def id_key(cls) -> str:
        """
        Key in the dictionary of the added/updated/deleted item that refers to the ID of
        that Item.
        """
        raise NotImplementedError("Implement in derived")

    @classmethod
    @abc.abstractmethod
    def summary_key(cls) -> str:
        """Key in the dictionary of the item that refers to its summary."""
        raise NotImplementedError("Implement in derived")

    @classmethod
    @abc.abstractmethod
    def last_modification_key(cls) -> str:
        """Key in the dictionary of the item that refers to its modification date."""
        raise NotImplementedError("Implement in derived")

    @final
    @classmethod
    def get_task_id(cls, item: ItemType) -> str:
        """Get the ID of a task in string form."""
        return str(item[cls.id_key])

    @final
    @classmethod
    def get_summary(cls, item: ItemType) -> str:
        """Get the summary of a task in string form."""
        return str(item[cls.summary_key])

    @classmethod
    @abc.abstractmethod
    def items_are_identical(
        cls, item1: ItemType, item2: ItemType, ignore_keys: Sequence[str] = []
    ) -> bool:
        """Determine whether two items are identical.

        .. returns:: True if items are identical, False otherwise.
        """
        raise NotImplementedError("Implement in derived")

    @final
    @staticmethod
    def _items_are_identical(item1: ItemType, item2: ItemType, keys: list) -> bool:
        """Compare the provided keys of the two given items.

        Take extra care of the datetime key.
        """

        for k in keys:
            if k not in item1 and k not in item2:
                continue

            if (k in item1 and k not in item2) or (k not in item1 and k in item2):
                logger.opt(lazy=True).trace(
                    f"Key [{k}] exists in one but not in other\n\n{item1}\n\n{item2}"
                )
                return False

            if isinstance(item1[k], datetime.datetime) and isinstance(
                item2[k], datetime.datetime
            ):
                if is_same_datetime(item1[k], item2[k], tol=datetime.timedelta(minutes=10)):
                    continue
                else:
                    logger.opt(lazy=True).trace(
                        f"\n\nItems differ\n\nItem1\n\n{item1}\n\nItem2\n\n{item2}"
                        f"\n\nKey [{k}] is different - [{repr(item1[k])}] | [{repr(item2[k])}]"
                    )
                    return False
            else:
                if item1[k] == item2[k]:
                    continue
                else:
                    logger.opt(lazy=True).trace(
                        f"\n\nItems differ\n\nItem1\n\n{item1}\n\nItem2\n\n{item2}"
                        f"\n\nKey [{k}] is different - [{repr(item1[k])}] | [{repr(item2[k])}]"
                    )
                    return False

        return True
