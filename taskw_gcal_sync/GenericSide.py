import abc
import datetime
from typing import Optional

from loguru import logger

from taskw_gcal_sync.helpers import is_same_datetime


class GenericSide(abc.ABC):
    """Interface for interacting with the various services."""

    def start(self):
        """Initialisation steps.

        Call this manually. Derived classes can take care of setting up data
        structures / connection, authentication requests etc.
        """
        pass

    @abc.abstractmethod
    def get_all_items(self, **kargs) -> list:
        """Query side and return a list of events

        :param kargs: Extra options for the call
        :return: A list of items. The type of these items depends on the derived
        class
        """
        raise NotImplementedError("Implement in derived")

    @abc.abstractmethod
    def get_item(self, item_id: str, use_cached: bool = False) -> Optional[dict]:
        """Get a single item based on the given UUID.

        :use_cached: False if you want to fetch the latest version of the item. True if a
                     cached version would do.
        :returns: None if not found, the item in dict representation otherwise
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def delete_single_item(self, item_id: str):
        """Delete an item based on the given UUID.

        .. raises:: Keyerror if item is not found.
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def update_item(self, item_id: str, **changes):
        """Update with the given item.

        :param item_id : ID of item to update
        :param changes: Keyword only parameters that are to change in the item
        .. warning:: The item must already be present
        """
        raise NotImplementedError("Should be implemented in derived")

    @abc.abstractmethod
    def add_item(self, item: dict) -> dict:
        """Add a new item.

        :returns: The newly added event
        """
        raise NotImplementedError("Implement in derived")

    @staticmethod
    def items_are_identical(item1: dict, item2: dict, ignore_keys=[]) -> bool:
        """Determine whether two items are identical.

        .. returns:: True if items are identical, False otherwise.
        """
        raise NotImplementedError("Implement in derived")

    @staticmethod
    def _items_are_identical(item1: dict, item2: dict, keys: list) -> bool:
        """Compare the provided keys of the two given items.

        Take extra care of the datetime key.
        """

        for k in keys:
            if k not in item1 and k not in item2:
                continue

            if (k in item1 and k not in item2) or (k not in item1 and k in item2):
                return False

            if isinstance(item1[k], datetime.datetime) and isinstance(
                item2[k], datetime.datetime
            ):
                if is_same_datetime(item1[k], item2[k]):
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
