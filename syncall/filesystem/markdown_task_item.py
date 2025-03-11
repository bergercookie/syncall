import datetime
import uuid

from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType


class MarkdownTaskItem(ConcreteItem):
    """A task line inside a Markdown file."""

    def __init__(self, is_checked: bool = False, title: str = ""):
        super().__init__(
            keys=(
                ItemKey("is_checked", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("title", KeyType.String),
            )
        )

        self.deleted = False
        self.is_checked = is_checked
        self.title = title

    @classmethod
    def from_raw_item(cls, markdown_raw_item: str) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the raw item at hand."""

        is_archived = False
        is_checked = False
        last_modified_date = None
        title = markdown_raw_item["title"]

        return cls(
            is_checked=is_checked,
            title=title,
        )

    def _id(self) -> ID:
        return uuid.uuid5(uuid.NAMESPACE_OID, self.title)

    def delete(self) -> None:
        self.deleted = True
