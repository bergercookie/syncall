import datetime
import re
import uuid

from item_synchronizer.types import ID

from syncall.concrete_item import ConcreteItem, ItemKey, KeyType
from syncall.filesystem.filesystem_file import FilesystemFile

MD_TASK_CHECKBOX_RE = r"-\s*\[[ xX]\]\s*"
MD_TASK_SCHEDULED_EMOJI = "⏳"
MD_TASK_DUE_EMOJI = "📅"
MD_TASK_DATE_RE = r"-\s*\[[ xX]\]\s*"

class MarkdownTaskItem(ConcreteItem):
    """A task line inside a Markdown file."""

    def __init__(self, is_checked: bool = False, title: str = ""):
        super().__init__(
            keys=(
                ItemKey("is_checked", KeyType.String),
                ItemKey("title", KeyType.String),
                ItemKey("last_modified_date", KeyType.Date),
            )
        )

        self.last_modified_date = None
        self.scheduled_date = None
        self.due_date = None
        self.deleted = False
        self.is_checked = is_checked
        self.title = title

    @classmethod
    def from_raw_item(cls, markdown_raw_item: str) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the raw item at hand."""

        result = cls(
            is_checked=markdown_raw_item["is_checked"],
            title=markdown_raw_item["title"]
        )
        # import pdb; pdb.set_trace()
        return result

    @classmethod
    def from_markdown(cls, markdown_text: str, markdown_file: FilesystemFile) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the line of text."""

        checkbox_found = re.match(MD_TASK_CHECKBOX_RE, markdown_text)
        if checkbox_found:
            is_checked = 'X' in checkbox_found.group(0).upper()
            title = re.split(MD_TASK_CHECKBOX_RE, markdown_text)[-1]

        result = cls(
            is_checked=is_checked,
            title=title
        )
        result.last_modified_date = markdown_file.last_modified_date
        # import pdb; pdb.set_trace()
        return result

    def __str__(self):
        return '- [{}] {}'.format(
            'X' if self.is_checked else ' ',
            self.title)

    @classmethod
    def last_modification_key(cls) -> str:
        return "last_modified_date"

    def _id(self) -> ID:
        return uuid.uuid5(uuid.NAMESPACE_OID, self.title)

    def delete(self) -> None:
        self.deleted = True
