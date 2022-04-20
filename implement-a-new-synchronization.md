# Implement a New Synchronization Service

There has been major refactoring in this software to make it more generic and
extendable and should hopefully be straightforward to support a new
synchronization between two arbitrary services using `syncall`. If
in doubt, have a look at an existing synchronization (e.g., `Taskwarrior`  <->
`Google Keep`) and mimic the way things are done there. That being said, you
should be comfortable with python before attempting to do so.

Let's say you want to implement synchronization of the items of service `alpha`,
with the items of service `beta`.

`syncall`, out-of-the-box, provides you with the following:

- A clear, well-tested framework, built on top of
  [item-synchronizer](https://github.com/bergercookie/item_synchronizer)
  to synchronize items of two arbitrary services.
- A mechanism to detect when a synchronization side contains modifications or
  additions and thus, trigger the right actions on the other side/service.
- Various resolution strategies to do the right thing in case of a conflict
  (e.g., an item modification on both synchronization sides) in a clear and
  flexible manner.
- Clear and detailed logging of the actions it's taking during the
  synchronization process and a summary of what's been done by the end of it. It
  also provides `-v`, -`vv` etc. flags to tweak the verbosity of the logging
  accordingly.

The following need to be done:

1. Implement a new top-level executable (`alpha_beta_sync.py`). Add a line about
   this executable in `pyproject.toml` (under `[tool.poetry.scripts]`) so that
   it's installed as part of the python package. See for example
   [tw_notion_sync](https://github.com/bergercookie/syncall/blob/master/syncall/scripts/tw_notion_sync.py).
   This executable should take care of setting the command line interface with
   the user of the tool, read credentials for connecting to the synchronization
   services, and most importantly invoke the
   [Aggregator](https://github.com/bergercookie/syncall/blob/master/syncall/aggregator.py).

   We're making use of `click` for CLI parsing across the top-level
   executables, and you can find command-line flags to re-use in the
   [app_utils](https://github.com/bergercookie/syncall/blob/master/syncall/app_utils.py)
   package.

1. Create a new Synchronization Side class for communicating with service
   `alpha` and a new synchronization Side class for communicating with service
   `beta`. If one of these sides already exists, e.g.,
   [NotionSide](https://github.com/bergercookie/syncall/blob/master/syncall/notion/notion_side.py),
   you can just reuse that.

   This class should implement the
   [SyncSide](https://github.com/bergercookie/syncall/blob/master/syncall/sync_side.py)
   abstract class and should abide to the following interface.

   ```py
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

   @classmethod
   @abc.abstractmethod
   def items_are_identical(
       cls, item1: ItemType, item2: ItemType, ignore_keys: Sequence[str] = []
   ) -> bool:
       """Determine whether two items are identical.

       .. returns:: True if items are identical, False otherwise.
       """
       raise NotImplementedError("Implement in derived")
   ```

   Note that items passed to and from the Side class are pure python
   dictionaries.

1. Create two conversion methods, one to convert an `alpha` item to a `beta`
   item, and a second one to convert a `beta` item to an `alpha` item. The
   convention is to name them `convert_tw_to_notion` and `convert_notion_to_tw`.
   These methods should be relatively short. See for example
   [tw_notion_utils](https://github.com/bergercookie/syncall/blob/master/syncall/tw_notion_utils.py).

You shouldn't need to tinker with:

- The
  [item-synchronizer/Synchronizer](https://github.com/bergercookie/item_synchronizer/blob/master/item_synchronizer/synchronizer.py)
  class. That's the meat of the synchronization process and it's independent of
  the sides that you want to synchronize.
- The
  [Aggregator](https://github.com/bergercookie/syncall/blob/master/syncall/aggregator.py)
  class. This sets the stage for calling the `Synchronizer` and
  should also be independent of the sides that you want to synchronize.
