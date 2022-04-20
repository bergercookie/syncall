"""Google Keep <-> Taskwarrior conversion functions"""
from bubop.time import format_datetime_tz

from syncall.google.gkeep_todo_item import GKeepTodoItem
from syncall.types import TwItem


def convert_tw_to_gkeep_todo(tw_item: TwItem) -> GKeepTodoItem:
    return GKeepTodoItem(
        is_checked=(tw_item["status"] == "completed"), plaintext=tw_item["description"]
    )


def convert_gkeep_todo_to_tw(gkeep_todo: GKeepTodoItem) -> TwItem:
    return {
        "status": "completed" if gkeep_todo.is_checked else "pending",
        "description": gkeep_todo.plaintext,
        "modified": format_datetime_tz(gkeep_todo.last_modified_date),
    }
