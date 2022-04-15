import gkeepapi
import pytest


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
def gkeep_note():
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
        "title": "A test note",
        "collaborators": [],
    }
