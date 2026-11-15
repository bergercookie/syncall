"""A task that was changed once must compare equal to its counterpart afterwards,
otherwise it is updated again on every run, alternating sides."""

import datetime

from icalendar import Todo
from syncall.caldav.caldav_utils import map_ics_to_item
from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide
from syncall.tw_caldav_utils import SYNCALL_TW_WAITING, convert_tw_to_caldav


def test_waiting_flag_is_read_back_from_caldav():
    tw_task = {"description": "t", "status": "pending", "uuid": "3925e236-3b27-4888-b41c-8c53610d722b"}
    sent = convert_tw_to_caldav(tw_task)
    todo = Todo()
    todo.add("uid", "x")
    todo.add("summary", "t")
    todo.add("status", "NEEDS-ACTION")
    todo.add(SYNCALL_TW_WAITING, sent[SYNCALL_TW_WAITING])
    assert map_ics_to_item(todo)[SYNCALL_TW_WAITING] == sent[SYNCALL_TW_WAITING]


def test_scheduled_only_on_one_side_is_not_a_difference():
    due = datetime.datetime(2026, 11, 30, 23, tzinfo=datetime.timezone.utc)
    task = {"description": "t", "status": "pending", "due": due, "uuid": "u",
            "scheduled": due - datetime.timedelta(days=1)}
    from_caldav = {k: v for k, v in task.items() if k != "scheduled"}
    assert TaskWarriorSide.items_are_identical(task, from_caldav)
    assert not TaskWarriorSide.items_are_identical(task, {**task, "scheduled": due})
