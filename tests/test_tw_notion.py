from typing import List

import pytest

from syncall.notion.notion_side import NotionSide
from syncall.notion.notion_todo_block import NotionTodoBlock
from syncall.tw_notion_utils import convert_notion_to_tw, convert_tw_to_notion
from syncall.types import NotionPageContents, NotionTodoBlockItem, TwItem, TwRawItem


# test conversions ----------------------------------------------------------------------------
def compare_items(notion_item: NotionTodoBlock, tw_item: TwItem):
    assert notion_item.plaintext == tw_item["description"]
    if notion_item.is_checked:
        assert tw_item["status"] == "completed"
    else:
        assert tw_item["status"] != "completed"


@pytest.mark.parametrize(
    "notion_todo",
    ["notion_simple_todo", "notion_chained_todo", "notion_simple_checked_todo"],
    indirect=True,
)
def test_convert_notion_to_tw(notion_todo: NotionTodoBlockItem):
    notion_todo_block = NotionTodoBlock.from_raw_item(notion_todo)
    tw_task = convert_notion_to_tw(notion_todo_block)
    compare_items(notion_todo_block, tw_task)


@pytest.mark.parametrize(
    "tw_task",
    ["tw_simple_pending_task", "tw_simple_completed_task"],
    indirect=True,
)
def test_convert_tw_to_notion(tw_task: TwRawItem):
    notion_todo_block = convert_tw_to_notion(tw_task[1])
    compare_items(notion_todo_block, tw_task[1])


# test page todo search -----------------------------------------------------------------------
def test_find_todos_in_page(page_contents: NotionPageContents):
    todos = NotionSide.find_todos(page_contents)
    assert len(todos) == 6
    is_checked: List[bool] = [True, False, False, False, False, False]
    is_archived: List[bool] = [False for _ in range(6)]
    plaintext: List[str] = [
        "Lacinato kale",
        "Bringing it back with style and glamour",
        "Highlight any text, and use the menu that pops up to style your writing however you"
        " like",
        "See the ⋮⋮ to the left of this checkbox on hover? Click and drag to move this line",
        "Click the + New Page button at the bottom of your sidebar to add a new page",
        "Click Templates in your sidebar to get started with pre-built pages",
    ]
    for i, todo in enumerate(todos):
        assert todo.is_checked == is_checked[i]
        assert todo.is_archived == is_archived[i]
        assert todo.plaintext == plaintext[i]
