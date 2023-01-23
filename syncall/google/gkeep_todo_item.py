import datetime

from gkeepapi.node import ListItem
from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType


class GKeepTodoItem(ConcreteItem):
    """A shim for the gkeepapi.node.ListItem."""

    def __init__(self, is_checked: bool = False, plaintext: str = ""):
        super().__init__(
            keys=(
                ItemKey("is_checked", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("plaintext", KeyType.String),
            )
        )

        # Embedding the ListItem as a member variable of this. The alternative of inheriting
        # from list item wouldnt' really work as that would require *copying* the ListItem for
        # creating the said GKeepTodoItem parent class and that wouldn't work with the
        # reference to the ListItme that GKeep already keeps.
        self._inner = ListItem()

        self.is_checked = is_checked
        self.plaintext = plaintext

    def _id(self) -> ID:
        return self._inner.id

    @classmethod
    def from_raw_item(cls, gkeep_raw_item: dict) -> "GKeepTodoItem":
        out = cls()
        out._inner.load(gkeep_raw_item)

        return out

    @property
    def is_checked(self):
        return self._inner.checked

    @is_checked.setter
    def is_checked(self, val):
        self._inner.checked = val

    @property
    def last_modified_date(self) -> datetime.datetime:
        return self._inner.timestamps.updated

    @property
    def plaintext(self) -> str:
        return self._inner.text

    @plaintext.setter
    def plaintext(self, val: str) -> None:
        self._inner.text = val

    @classmethod
    def from_gkeep_list_item(cls, list_item: ListItem) -> "GKeepTodoItem":
        out = cls()
        out._inner = list_item
        return out

    def delete(self) -> None:
        self._inner.delete()
