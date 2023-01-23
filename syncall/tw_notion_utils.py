"""Notion-related utils."""
import datetime
from typing import cast

from bubop import format_datetime_tz, parse_datetime
from notion_client import Client

from syncall.notion.notion_todo_block import NotionTodoBlock
from syncall.types import NotionPage, TwItem


def create_page(parent_page_id: str, title: str, client: Client) -> NotionPage:
    return cast(
        NotionPage,
        client.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": [{"text": {"content": title}}],
            },
            children=[],
        ),
    )


def convert_tw_to_notion(tw_item: TwItem) -> NotionTodoBlock:
    modified = tw_item["modified"]
    if isinstance(modified, datetime.datetime):
        dt = modified
    else:
        dt = parse_datetime(modified)

    return NotionTodoBlock(
        is_archived=False,
        is_checked=tw_item["status"] == "completed",
        plaintext=tw_item["description"],
        last_modified_date=dt,
    )


def convert_notion_to_tw(todo_block: NotionTodoBlock) -> TwItem:
    return {
        "status": "completed" if todo_block.is_checked else "pending",
        "description": todo_block.plaintext,
        "modified": format_datetime_tz(todo_block.last_modified_date),
    }
