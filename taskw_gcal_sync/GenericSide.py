import abc
import logging
from taskw_gcal_sync.clogger import setup_logging
from typing import Dict, Union

class GenericSide():
    """Interface for interacting with the various services.

    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(GenericSide, self).__init__()

        logger_name = self.__class__.__name__
        self.logger = logging.getLogger(logger_name)
        setup_logging(logger_name)

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

    def get_single_item(self, _id: str) -> Union[dict, None]:
        """Get a single item based on the given UUID.

        :returns: None if not found, the item in dict representation otherwise
        """
        raise NotImplementedError("Should be implemented in derived")

    def update_items(self, item_changes: Dict[str, dict]) -> bool:
        """Update the db with the given items

        This constitudes a wrapper around the `update_item` method.

        :param items: dict of (item_id, item) with which to update the
                      side of the derived class.
        :return: True if changes were successfully applied
        """
        for _id, changes in item_changes.items():
            ret = self.update_item(_id, **changes)
            if not ret:
                return ret

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
