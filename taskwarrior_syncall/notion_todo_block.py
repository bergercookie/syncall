import datetime
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from bubop import is_same_datetime, logger, parse_datetime

from taskwarrior_syncall.types import (
    NotionID,
    NotionRawItem,
    NotionTodoBlockItem,
    NotionTodoSection,
)


@dataclass
class NotionTodoBlock(Mapping):
    is_archived: bool
    is_checked: bool
    last_modified_date: datetime.datetime
    plaintext: str
    id: Optional[NotionID] = None

    _key_names = {
        "is_archived",
        "is_checked",
        "last_modified_date",
        "plaintext",
        "id",
    }

    _date_key_names = {"last_modified_date"}

    def compare(self, other: "NotionTodoBlock", ignore_keys: Sequence[str] = []) -> bool:
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

    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def __iter__(self):
        for k in self._key_names:
            yield k

    def __len__(self):
        return len(self._key_names)

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

        return NotionTodoBlock(
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
