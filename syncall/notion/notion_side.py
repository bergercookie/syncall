from typing import Dict, Optional, Sequence, cast

from bubop import logger
from notion_client import Client

from syncall.notion.notion_todo_block import NotionTodoBlock
from syncall.sync_side import SyncSide
from syncall.types import NotionID, NotionPageContents, NotionTodoBlockItem


class NotionSide(SyncSide):
    """
    Wrapper class to add/modify/delete todo blocks from notion, create new pages, etc.
    """

    _date_keys = "last_modified_date"

    def __init__(self, client: Client, page_id: NotionID):
        self._client = client
        self._page_id = page_id
        self._page_contents: NotionPageContents
        self._all_todo_blocks: Dict[NotionID, NotionTodoBlock]
        self._is_cached = False

        super().__init__(name="Notion", fullname="Notion")

    @classmethod
    def id_key(cls) -> str:
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        return "plaintext"

    @classmethod
    def last_modification_key(cls) -> str:
        return "last_modified_date"

    def start(self):
        logger.info(f"Initializing {self.fullname}...")
        self._page_contents = self._client.blocks.children.list(block_id=self._page_id)

    def _get_todo_blocks(self) -> Dict[NotionID, NotionTodoBlock]:
        all_todos = self.find_todos(page_contents=self._page_contents)
        # make sure that all IDs are valid and not None
        assert all([todo.id is not None for todo in all_todos])

        return {cast(NotionID, todo.id): todo for todo in all_todos}

    def get_all_items(self, **kargs) -> Sequence[NotionTodoBlock]:
        self._all_todo_blocks = self._get_todo_blocks()
        self._is_cached = True

        return tuple(self._all_todo_blocks.values())

    def get_item(
        self, item_id: NotionID, use_cached: bool = False
    ) -> Optional[NotionTodoBlock]:
        """Return a single todo block"""
        if use_cached:
            return self._all_todo_blocks.get(item_id)

        # have to fetch and cache it again
        new_todo_block_item: NotionTodoBlockItem = self._client.blocks.retrieve(item_id)
        try:
            new_todo_block = NotionTodoBlock.from_raw_item(new_todo_block_item)
        except RuntimeError:
            # the to_do section is missing when the item is archived?!
            raise KeyError

        assert new_todo_block.id is not None
        self._all_todo_blocks[new_todo_block.id] = new_todo_block

        return new_todo_block

    def delete_single_item(self, item_id: NotionID):
        """Delete a single block."""
        self._client.blocks.delete(item_id)

    def get_vanilla_notion_todo_section(self, text: str, is_checked: bool) -> dict:
        return {
            "text": [{"type": "text", "text": {"content": text}}],
            "checked": is_checked,
        }

    def update_item(self, item_id: NotionID, **updated_properties):
        if not {"plaintext", "is_checked"}.issubset(updated_properties.keys()):
            logger.warning(f"Invalid changes provided to Notion Side -> {updated_properties}")
            return

        updated_todo = self.get_vanilla_notion_todo_section(
            text=updated_properties["plaintext"], is_checked=updated_properties["is_checked"]
        )
        self._client.blocks.update(block_id=item_id, to_do=updated_todo)

    def add_item(self, item: NotionTodoBlock) -> NotionTodoBlock:
        """Add a new item (block) to the page."""
        page_contents: NotionPageContents = self._client.blocks.children.append(
            block_id=self._page_id, children=[item.serialize()]
        )
        todo_blocks = self.find_todos(page_contents=page_contents)
        if len(todo_blocks) != 1:
            logger.warning(
                "Expected to get back 1 TODO item, blocks.children.append(...) returned"
                f" {len(todo_blocks)} items. Adding only the first"
            )

        return todo_blocks[0]

    def add_todo_block(self, title: str, checked: bool = False) -> NotionTodoBlock:
        """Create a new TODO block with the given title."""
        new_block = {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "text": [{"type": "text", "text": {"content": title}}],
                "checked": checked,
            },
        }
        raw_item = self._client.blocks.children.append(
            block_id=self._page_id, children=[new_block]
        )
        return NotionTodoBlock.from_raw_item(raw_item)

    @classmethod
    def items_are_identical(
        cls, item1: NotionTodoBlock, item2: NotionTodoBlock, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = [cls.last_modification_key()]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)

    @staticmethod
    def find_todos(page_contents: NotionPageContents) -> Sequence[NotionTodoBlock]:
        assert page_contents["object"] == "list"
        todos = tuple(
            NotionTodoBlock.from_raw_item(cast(NotionTodoBlockItem, block))
            for block in page_contents["results"]
            if NotionTodoBlock.is_todo(block)
        )

        return todos
