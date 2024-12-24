import datetime

from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType


class MarkdownTaskItem(ConcreteItem):
    """A task line inside a Markdown file."""

    def __init__(self, line):
        super().__init__(
            keys=(
                ItemKey("is_checked", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
                ItemKey("plaintext", KeyType.String),
            )
        )

        # TODO
        self.is_checked = True
        self.last_modified_date = None
        self.plaintext = line
        self.deleted = False

    @classmethod
    def from_raw_item(cls, markdown_raw_item: str) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the raw item at hand."""

        is_archived = False
        is_checked = False
        self.last_modified_date = None
        plaintext = markdown_raw_item

        return cls(
            is_archived=is_archived,
            is_checked=is_checked,
            last_modified_date=last_modified_date,
            plaintext=plaintext,
            id=id_,
        )


    @property
    def is_checked(self):
        return self.is_checked

    @is_checked.setter
    def is_checked(self, val):
        self.is_checked = val

    @property
    def last_modified_date(self) -> datetime.datetime:
        return datetime.datetime.today()

    @property
    def plaintext(self) -> str:
        return self.plaintext

    @plaintext.setter
    def plaintext(self, val: str) -> None:
        self.plaintext = val

    def delete(self) -> None:
        self.deleted = True
