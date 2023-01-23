import pytest
from gkeepapi.node import List, Note

from syncall.google.gkeep_note import GKeepNote as MyGKeepNote


@pytest.fixture()
def gkeep_raw_item(request: pytest.FixtureRequest) -> dict:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return request.getfixturevalue(param)


@pytest.fixture()
def gkeep_simple_done_item():
    return {
        "id": "17dfc18a2f3.8741b729cb5c4951",
        "kind": "notes#node",
        "type": "LIST_ITEM",
        "parentId": "1537610635503.986093470",
        "sortValue": "985162488741890",
        "baseVersion": "1",
        "text": "Φέτα Καλαβρύτων",
        "serverId": "18TyfHj4ojXe0nnIkktldiBpP-rwQI-Fr6G-vKBFhVURTSCpLtj1pYlNeemimOp-N5Go",
        "timestamps": {
            "kind": "notes#timestamps",
            "created": "2021-12-27T13:33:53.073000Z",
            "updated": "2021-12-28T17:42:26.433000Z",
        },
        "nodeSettings": {
            "newListItemPlacement": "BOTTOM",
            "graveyardState": "EXPANDED",
            "checkedListItemsPolicy": "GRAVEYARD",
        },
        "annotationsGroup": {"kind": "notes#annotationsGroup"},
        "parentServerId": None,
        "superListItemId": None,
        "checked": True,
    }


@pytest.fixture()
def gkeep_simple_pending_item():
    return {
        "id": "17dfc186465.a997b5c8c22e6d95",
        "kind": "notes#node",
        "type": "LIST_ITEM",
        "parentId": "1537610635503.986093470",
        "sortValue": "562950234439681",
        "baseVersion": "1",
        "text": "Σαμπάνια",
        "serverId": "1jpSvn_LGyHrfksCtFWuT2VB3L35GyX_tUsje6IJziyiuQrzSRMv8XdbOVO3JHDPi-gA",
        "timestamps": {
            "kind": "notes#timestamps",
            "created": "2021-12-27T13:33:53.073000Z",
            "updated": "2021-12-27T13:33:53.073000Z",
        },
        "nodeSettings": {
            "newListItemPlacement": "BOTTOM",
            "graveyardState": "EXPANDED",
            "checkedListItemsPolicy": "GRAVEYARD",
        },
        "annotationsGroup": {"kind": "notes#annotationsGroup"},
        "parentServerId": None,
        "superListItemId": None,
        "checked": False,
    }


@pytest.fixture()
def gkeep_list0():
    return {
        "id": "1640713336402.1772858868",
        "kind": "notes#node",
        "type": "LIST",
        "parentId": "root",
        "sortValue": "97517568",
        "text": "",
        "serverId": "135LPjTrC6tsfxrYPjM9htohkMc2U0WsNNbqRCmNbJMlvREQrcp9GozuddiEZ6g",
        "timestamps": {
            "kind": "notes#timestamps",
            "created": "2021-12-29T06:53:19.851000Z",
            "trashed": "1970-01-01T00:00:00.000000Z",
            "updated": "2021-12-29T06:53:57.075000Z",
            "userEdited": "2021-12-29T06:53:56.932000Z",
        },
        "nodeSettings": {
            "newListItemPlacement": "BOTTOM",
            "graveyardState": "EXPANDED",
            "checkedListItemsPolicy": "GRAVEYARD",
        },
        "annotationsGroup": {"kind": "notes#annotationsGroup"},
        "color": "DEFAULT",
        "isArchived": False,
        "isPinned": False,
        "title": "A test list",
        "collaborators": [],
    }


@pytest.fixture()
def gkeep_list1():
    return {
        "id": "17bb5ae1fb8.7ce1b3ded4d6a3f7",
        "kind": "notes#node",
        "type": "LIST",
        "parentId": "root",
        "sortValue": "5890307729",
        "text": "",
        "serverId": "1xe7OcSNBXzMVbPU3PRCYslPq75uM5M0dKMhIBkHK43xi8pyiHD2j0cAI9QgoUIfSj2aB",
        "timestamps": {
            "kind": "notes#timestamps",
            "created": "2021-09-05T11:18:13.282000Z",
            "trashed": "1970-01-01T00:00:00.000000Z",
            "updated": "2021-09-05T11:24:55.822000Z",
            "userEdited": "2021-09-05T11:24:55.720000Z",
        },
        "nodeSettings": {
            "newListItemPlacement": "BOTTOM",
            "graveyardState": "COLLAPSED",
            "checkedListItemsPolicy": "GRAVEYARD",
        },
        "annotationsGroup": {
            "kind": "notes#annotationsGroup",
            "annotations": [
                {
                    "id": "f4c1a837-0f6f-4b3f-a34c-b163817f9259",
                    "topicCategory": {"category": "FOOD"},
                }
            ],
        },
        "color": "RED",
        "isArchived": False,
        "isPinned": True,
        "title": "Todo",
        "collaborators": [],
    }


@pytest.fixture()
def gkeep_note_empty():
    return {
        "id": "1630840404258.423492350",
        "kind": "notes#node",
        "type": "NOTE",
        "parentId": "root",
        "sortValue": "78643201",
        "text": "",
        "serverId": "14rOB8irunIXU-0XMY8DLLqT2vNaPsFFRKO1MfYg-KXWrrYYG_boCioHhcPy6IQ",
        "timestamps": {
            "kind": "notes#timestamps",
            "created": "2021-09-05T11:13:30.881000Z",
            "trashed": "1970-01-01T00:00:00.000000Z",
            "updated": "2021-09-05T11:14:21.868000Z",
            "userEdited": "2021-09-05T11:13:53.176000Z",
        },
        "nodeSettings": {
            "newListItemPlacement": "BOTTOM",
            "graveyardState": "EXPANDED",
            "checkedListItemsPolicy": "GRAVEYARD",
        },
        "annotationsGroup": {"kind": "notes#annotationsGroup"},
        "color": "TEAL",
        "isArchived": False,
        "isPinned": False,
        "title": "a sample note without checkboxes",
        "labelIds": [
            {
                "labelId": "tag.qr30ughe2zk6.1630840458798",
                "deleted": "1970-01-01T00:00:00.000000Z",
            }
        ],
        "collaborators": [],
    }


@pytest.fixture()
def gkeep_list_instance0(gkeep_list0: List) -> List:
    li = List()
    li.load(gkeep_list0)

    for i in range(5):
        li.add(f"item {i}")

    return li


@pytest.fixture()
def gkeep_note_empty_instance(gkeep_note_empty: dict) -> MyGKeepNote:
    note = MyGKeepNote.from_raw_item(gkeep_note_empty)
    return note


@pytest.fixture()
def gkeep_note_instance(gkeep_note_empty_instance: MyGKeepNote) -> MyGKeepNote:
    note = gkeep_note_empty_instance
    note.plaintext = """Some multi
line
text

with some empty lines as well
as emojis
😄
    """

    return note
