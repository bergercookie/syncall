import datetime

from gkeepapi.node import Note
from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType


class GKeepNote(ConcreteItem):
    """A shim for the gkeepapi.node.Note.

    If the item is of type gkeepapi.node.List then the conversion to node.Note should be
    handled beforehand.
    """

    def __init__(self, plaintext: str = "", title: str = ""):
        super().__init__(
            keys=(
                ItemKey("plaintext", KeyType.String),
                ItemKey("title", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("is_deleted", KeyType.Boolean),
            )
        )

        self._inner: Note = Note()
        self.plaintext = plaintext
        self.title = title

    def _id(self) -> ID:
        return self._inner.id

    @classmethod
    def from_raw_item(cls, gkeep_raw_item: dict) -> "GKeepNote":
        out = cls()
        out._inner.load(gkeep_raw_item)
        return out

    @classmethod
    def from_gkeep_note(cls, note_item: Note) -> "GKeepNote":
        out = cls()
        out._inner = note_item
        return out

    @property
    def last_modified_date(self) -> datetime.datetime:
        return self._inner.timestamps.updated

    @property
    def plaintext(self) -> str:
        return self._inner.text

    @plaintext.setter
    def plaintext(self, val: str) -> None:
        self._inner.text = val

    @property
    def title(self) -> str:
        return self._inner.title

    @title.setter
    def title(self, val: str) -> None:
        self._inner.title = val

    def delete(self) -> None:
        self._inner.trash()

    def undelete(self) -> None:
        self._inner.untrash()

    @property
    def is_deleted(self) -> bool:
        return self._inner.trashed

    @is_deleted.setter
    def is_deleted(self, val: bool) -> None:
        if val is True:
            self.delete()
        else:
            self.undelete()
