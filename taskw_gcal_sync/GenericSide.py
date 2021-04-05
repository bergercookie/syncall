import abc
import datetime
from typing import Union

from taskw_gcal_sync.utils import is_same_datetime


class GenericSide(abc.ABC):
    """Interface for interacting with the various services."""

    __metaclass__ = abc.ABCMeta

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
    def get_single_item(self, item_id: str) -> Union[dict, None]:
        """Get a single item based on the given UUID.

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
            if k in item1 and k in item2:
                if isinstance(item1[k], datetime.datetime) and isinstance(
                    item2[k], datetime.datetime
                ):

                    if is_same_datetime(item1[k], item2[k]):
                        continue
                    else:
                        return False

                else:
                    if item1[k] == item2[k]:
                        continue
                    else:
                        return False

            elif k not in item1 and k not in item2:
                continue
            else:
                return False

        return True
