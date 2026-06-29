import datetime
import re
import uuid

from typing import Optional

from item_synchronizer.types import ID
from syncall.concrete_item import ConcreteItem, ItemKey, KeyType
from syncall.filesystem.filesystem_file import FilesystemFile

MD_TASK_CHECKBOX_RE = r"\[[ xX]\]"
MD_TASK_LINE_START_RE = r"-\s*" + MD_TASK_CHECKBOX_RE
MD_TASK_SCHEDULED_EMOJI = "⏳"
MD_TASK_DUE_EMOJI = "📅"
MD_TASK_DONE_EMOJI = "✅"

MD_TASK_DATE_RE = r"(?<={EMOJI} )\d{4}-\d{2}-\d{2}"

MD_TASK_SCHEDULED_RE = MD_TASK_DATE_RE.replace('{EMOJI}', MD_TASK_SCHEDULED_EMOJI)
MD_TASK_DUE_RE = MD_TASK_DATE_RE.replace('{EMOJI}', MD_TASK_DUE_EMOJI)
MD_TASK_DONE_RE = MD_TASK_DATE_RE.replace('{EMOJI}', MD_TASK_DONE_EMOJI)

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

        self._persistent_id = None
        self.last_modified_date = None
        self.scheduled_date = None
        self.due_date = None
        self.done_date = None
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
        return result

    @classmethod
    def from_markdown(cls, markdown_text: str, markdown_file: FilesystemFile) -> "MarkdownTaskItem":
        """Create a MarkdownTaskItem given the line of text."""

        markdown_task = re.match(MD_TASK_LINE_START_RE, markdown_text)

        if markdown_task is None:
            return None

        checkbox_found = re.search(MD_TASK_CHECKBOX_RE, markdown_text)
        is_checked = 'X' in checkbox_found.group(0).upper()

        md_task_split_re = "(\\s*{}\\s*|\\s*{}\\s*|\\s*{}\\s*|\\s*{}\\s*)".format(MD_TASK_CHECKBOX_RE, MD_TASK_SCHEDULED_EMOJI, MD_TASK_DUE_EMOJI, MD_TASK_DONE_EMOJI)
        title = re.split(md_task_split_re, markdown_text)[2].strip()

        result = cls(
            is_checked=is_checked,
            title=title
        )
        result.last_modified_date = markdown_file.last_modified_date

        due_date = re.search(MD_TASK_DUE_RE, markdown_text)
        scheduled_date = re.search(MD_TASK_SCHEDULED_RE, markdown_text)
        done_date = re.search(MD_TASK_DONE_RE, markdown_text)

        if due_date:
            result.due_date = datetime.datetime.fromisoformat(due_date.group(0))

        if scheduled_date:
            result.scheduled_date = datetime.datetime.fromisoformat(scheduled_date.group(0))

        if done_date:
            result.done_date = datetime.datetime.fromisoformat(done_date.group(0))

        return result

    def __str__(self):
        result = '- [{}] {}'.format(
            'X' if self.is_checked else ' ',
            self.title)

        if self.scheduled_date:
            result += " " + MD_TASK_SCHEDULED_EMOJI + " " + self.scheduled_date.date().isoformat()

        if self.due_date:
            result += " " + MD_TASK_DUE_EMOJI + " " + self.due_date.date().isoformat()

        if self.done_date:
            result += " " + MD_TASK_DONE_EMOJI + " " + self.done_date.date().isoformat()

        return result

    def _id(self) -> ID:
        return uuid.uuid5(uuid.NAMESPACE_OID, self.title)

    @property
    def id(self) -> Optional[ID]:
        return self._persistent_id or self._id()

    def delete(self) -> None:
        self.deleted = True
