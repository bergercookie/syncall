import pytest

from syncall.tw_gtasks_utils import convert_gtask_to_tw, convert_tw_to_gtask
from syncall.types import GTasksItem, TwItem, TwRawItem


# test conversions ----------------------------------------------------------------------------
def compare_items(gtasks_item: GTasksItem, tw_item: TwItem):
    assert gtasks_item["title"] == tw_item["description"]
    if "status" in tw_item.keys():
        if gtasks_item["status"] == "completed":
            assert tw_item["status"] == "completed"
        else:
            assert tw_item["status"] != "completed"


@pytest.mark.parametrize(
    "gtask",
    [
        "gtasks_simple_done_item",
        "gtasks_simple_pending_item",
    ],
    indirect=True,
)
def test_convert_gtask_to_tw(gtask: GTasksItem):
    tw_task = convert_gtask_to_tw(gtask)
    compare_items(gtask, tw_task)


@pytest.mark.parametrize(
    "tw_task",
    ["tw_pending_task", "tw_completed_task"],
    indirect=True,
)
def test_convert_tw_to_gtask(tw_task: TwItem):
    gtask_item = convert_tw_to_gtask(tw_task)
    compare_items(gtask_item, tw_task)
