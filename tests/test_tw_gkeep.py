import pytest
from bubop.time import format_datetime_tz

from syncall import GKeepTodoItem
from syncall.tw_gkeep_utils import convert_gkeep_todo_to_tw, convert_tw_to_gkeep_todo
from syncall.types import TwItem, TwRawItem


# test conversions ----------------------------------------------------------------------------
def compare_items(gkeep_item: GKeepTodoItem, tw_item: TwItem):
    assert gkeep_item.plaintext == tw_item["description"]
    if gkeep_item.is_checked:
        assert tw_item["status"] == "completed"
    else:
        assert tw_item["status"] != "completed"


@pytest.mark.parametrize(
    "gkeep_raw_item",
    ["gkeep_simple_pending_item", "gkeep_simple_done_item"],
    indirect=True,
)
def test_convert_gkeep_to_tw(gkeep_raw_item: dict):
    gkeep_item = GKeepTodoItem.from_raw_item(gkeep_raw_item)
    tw_task = convert_gkeep_todo_to_tw(gkeep_item)
    compare_items(gkeep_item, tw_task)


@pytest.mark.parametrize(
    "tw_task",
    ["tw_simple_pending_task", "tw_simple_completed_task"],
    indirect=True,
)
def test_convert_tw_to_gkeep_todo(tw_task: TwRawItem):
    gkeep_item = convert_tw_to_gkeep_todo(tw_task[1])
    compare_items(gkeep_item, tw_task[1])


@pytest.mark.parametrize(
    "gkeep_raw_item",
    ["gkeep_simple_pending_item", "gkeep_simple_done_item"],
    indirect=True,
)
def test_gkeep_todo_item_creation_from_raw(gkeep_raw_item):
    gkeep_item = GKeepTodoItem.from_raw_item(gkeep_raw_item)
    assert gkeep_item.is_checked == gkeep_raw_item["checked"]
    assert gkeep_item.id == gkeep_raw_item["id"]
    assert gkeep_item.plaintext == gkeep_raw_item["text"]
    assert (
        format_datetime_tz(gkeep_item.last_modified_date)
        == gkeep_raw_item["timestamps"]["updated"]
    )
