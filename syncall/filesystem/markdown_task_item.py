import datetime
import uuid

from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType


class MarkdownTaskItem(ConcreteItem):
    """A task line inside a Markdown file."""

    def __init__(self, line):
        super().__init__(
            keys=(
                ItemKey("is_checked", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("title", KeyType.String),
            )
        )

        self.deleted = False

    @classmethod
    def from_raw_item(cls, markdown_raw_item: str) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the raw item at hand."""

        is_archived = False
        is_checked = False
        self.last_modified_date = None
        title = markdown_raw_item

        return cls(
            is_checked=is_checked,
            last_modified_date=last_modified_date,
            title=title,
        )

    @property
    def id(self) -> ID:
        return uuid.uuid3('ID', self.text)

    def delete(self) -> None:
        self.deleted = True
