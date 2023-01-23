import datetime

from dateutil.tz import tzutc

from syncall.concrete_item import ItemKey, KeyType
from syncall.notion.notion_todo_block import NotionTodoBlock
from syncall.types import NotionTodoBlockItem

simple_last_modified_date = datetime.datetime(2021, 12, 4, 10, 1, tzinfo=tzutc())
chained_last_modified_date = datetime.datetime(2021, 12, 4, 11, 30, tzinfo=tzutc())


def test_notion_todo_block_compare0(notion_simple_todo: NotionTodoBlockItem):
    n = NotionTodoBlock.from_raw_item(notion_simple_todo)
    assert n.compare(n)


def test_notion_todo_block_compare1(
    notion_simple_todo: NotionTodoBlockItem, notion_chained_todo: NotionTodoBlockItem
):
    n0 = NotionTodoBlock.from_raw_item(notion_simple_todo)
    n1 = NotionTodoBlock.from_raw_item(notion_chained_todo)
    assert not n0.compare(n1)


def test_notion_todo_block_compare2(
    notion_simple_todo: NotionTodoBlockItem, notion_simple_checked_todo: NotionTodoBlockItem
):
    n0 = NotionTodoBlock.from_raw_item(notion_simple_todo)
    n1 = NotionTodoBlock.from_raw_item(notion_simple_checked_todo)
    assert not n0.compare(n1)
    assert n0.compare(n1, ignore_keys=[ItemKey(name="is_checked", type=KeyType.Boolean)])


def test_notion_todo_block_compare3(
    notion_simple_todo: NotionTodoBlockItem, notion_simple_archived_todo: NotionTodoBlockItem
):
    n0 = NotionTodoBlock.from_raw_item(notion_simple_todo)
    n1 = NotionTodoBlock.from_raw_item(notion_simple_archived_todo)
    assert not n0.compare(n1)
    assert n0.compare(n1, ignore_keys=[ItemKey(name="is_archived", type=KeyType.Boolean)])


def test_notion_todo_block_compare4(
    notion_simple_todo: NotionTodoBlockItem,
    notion_simple_diff_edited_time_todo: NotionTodoBlockItem,
):
    n0 = NotionTodoBlock.from_raw_item(notion_simple_todo)
    n1 = NotionTodoBlock.from_raw_item(notion_simple_diff_edited_time_todo)
    assert not n0.compare(n1)
    assert n0.compare(n1, ignore_keys=[ItemKey(name="last_modified_date", type=KeyType.Date)])


def test_notion_todo_block0(notion_simple_todo: NotionTodoBlockItem):
    todo_block = NotionTodoBlock.from_raw_item(notion_simple_todo)
    assert todo_block.plaintext == "Lacinato kale"
    assert todo_block.is_checked == False
    assert todo_block.is_archived == False
    assert todo_block.last_modified_date == simple_last_modified_date
    assert todo_block.id == "7de89eb6-4ee1-472c-abcd-8231049e9d8d"


def test_notion_todo_block1(notion_chained_todo: NotionTodoBlockItem):
    todo_block = NotionTodoBlock.from_raw_item(notion_chained_todo)
    assert todo_block.plaintext == "Bringing it back with style and glamour"
    assert todo_block.is_checked == False
    assert todo_block.is_archived == False
    assert todo_block.last_modified_date == chained_last_modified_date
    assert todo_block.id == "9146e728-d7c4-4678-bab4-377a3991ebb8"


def test_notion_todo_block2(notion_simple_checked_todo: NotionTodoBlockItem):
    todo_block = NotionTodoBlock.from_raw_item(notion_simple_checked_todo)
    assert todo_block.plaintext == "Lacinato kale"
    assert todo_block.is_checked == True
    assert todo_block.is_archived == False
    assert todo_block.last_modified_date == simple_last_modified_date
    assert todo_block.id == "7de89eb6-4ee1-472c-abcd-8231049e9d8d"


def test_notion_todo_block3(notion_simple_archived_todo: NotionTodoBlockItem):
    todo_block = NotionTodoBlock.from_raw_item(notion_simple_archived_todo)
    assert todo_block.plaintext == "Lacinato kale"
    assert todo_block.is_checked == False
    assert todo_block.is_archived == True
    assert todo_block.last_modified_date == simple_last_modified_date
    assert todo_block.id == "7de89eb6-4ee1-472c-abcd-8231049e9d8d"
