import datetime
from typing import Optional

from bubop import is_same_datetime, logger, parse_datetime
from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType
from syncall.types import NotionRawItem, NotionTodoBlockItem, NotionTodoSection


class NotionTodoBlock(ConcreteItem):
    def __init__(
        self,
        is_archived: bool,
        is_checked: bool,
        last_modified_date: datetime.datetime,
        plaintext: str,
        id: Optional[ID] = None,
    ):
        super().__init__(
            keys=(
                ItemKey("is_archived", KeyType.Boolean),
                ItemKey("is_checked", KeyType.Boolean),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("plaintext", KeyType.String),
            )
        )

        self._is_archived = is_archived
        self._is_checked = is_checked
        self._last_modified_date = last_modified_date
        self._plaintext = plaintext
        self._id_val = id

    @property
    def is_archived(self) -> bool:
        return self._is_archived

    @is_archived.setter
    def is_archived(self, val):
        self._is_archived = val

    @property
    def is_checked(self) -> bool:
        return self._is_checked

    @is_checked.setter
    def is_checked(self, val):
        self._is_checked = val

    @property
    def last_modified_date(self) -> datetime.datetime:
        return self._last_modified_date

    @last_modified_date.setter
    def last_modified_date(self, val: datetime.datetime):
        self._last_modified_date = val

    def _id(self) -> Optional[ID]:
        return self._id_val

    @classmethod
    def from_raw_item(cls, block_item: NotionTodoBlockItem) -> "NotionTodoBlock":
        """Create a NotionTodoBlock given the raw item at hand."""
        assert "archived" in block_item
        assert "id" in block_item
        assert "last_edited_time" in block_item
        assert "object" in block_item
        assert block_item["object"] == "block"

        if "to_do" not in block_item:
            logger.exception("This is not a to_do block")
            raise RuntimeError

        id_ = block_item["id"]
        is_archived = block_item["archived"]
        is_checked = block_item["to_do"]["checked"]
        last_modified_date = parse_datetime(block_item["last_edited_time"])
        plaintext = cls.get_plaintext(todo_section=block_item["to_do"])

        return cls(
            is_archived=is_archived,
            is_checked=is_checked,
            last_modified_date=last_modified_date,
            plaintext=plaintext,
            id=id_,
        )

    @classmethod
    def is_todo(cls, item: NotionRawItem) -> bool:
        """Parse the given block."""
        if not {"type", "object"}.issubset(item.keys()) or item["object"] != "block":
            return False
        return item["type"] == "to_do"

    @property
    def plaintext(self):
        return self._plaintext

    @plaintext.setter
    def plaintext(self, val):
        self._plaintext = val

    @classmethod
    def get_plaintext(cls, todo_section: NotionTodoSection):
        """Get the plaintext from a todo section."""
        return "".join([li["plain_text"] for li in todo_section["text"]])  # type: ignore

    def serialize(self) -> dict:
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "text": [{"type": "text", "text": {"content": self.plaintext}}],
                "checked": self.is_checked,
            },
        }
