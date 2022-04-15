import datetime
from typing import Any, Mapping, Sequence

from bubop.time import is_same_datetime
from gkeepapi.node import ListItem
from item_synchronizer.types import ID
from loguru import logger


# GKeepTodoSide
class GKeepTodoItem(Mapping):
    """Currently a shim for the gkeepapi.node.ListItem.

    Exposes a similar API to the NotionTodoBlock class.
    """

    _key_names = {
        "is_checked",
        "last_modified_date",
        "plaintext",
        "id",
    }

    _date_key_names = {"last_modified_date"}

    def __init__(self, is_checked: bool = False, plaintext: str = ""):
        super().__init__()

        # Embedding the ListItem as a member variable of this. The alternative of inheriting
        # from list item wouldnt' really work as that would require *copying* the ListItem for
        # creating the said GKeepTodoItem parent class and that wouldn't work with the
        # reference to the ListItme that GKeep already keeps.
        self._inner = ListItem()

        self.is_checked = is_checked
        self.plaintext = plaintext

    @property
    def id(self) -> ID:
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

    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def __iter__(self):
        for k in self._key_names:
            yield k

    def __len__(self):
        return len(self._key_names)

    def delete(self) -> None:
        self._inner.delete()

    def compare(self, other: "GKeepTodoItem", ignore_keys: Sequence[str] = []) -> bool:
        """Compare two items, return True if they are considered equal."""
        for key in self._key_names:
            if key in ignore_keys:
                continue
            elif key in self._date_key_names:
                if not is_same_datetime(
                    self[key], other[key], tol=datetime.timedelta(minutes=10)
                ):
                    logger.opt(lazy=True).trace(
                        f"\n\nItems differ\n\nItem1\n\n{self}\n\nItem2\n\n{other}\n\nKey"
                        f" [{key}] is different - [{repr(self[key])}] | [{repr(other[key])}]"
                    )
                    return False
            else:
                if self[key] != other[key]:
                    logger.opt(lazy=True).trace(f"Items differ [{key}]\n\n{self}\n\n{other}")
                    return False

        return True
