import os
from typing import Sequence

import pytest

from syncall.filesystem.filesystem_file import FilesystemFile
from syncall.filesystem.filesystem_side import FilesystemSide


@pytest.mark.parametrize(
    "fs_side",
    ["fs_side_no_items", "fs_side_with_existing_items"],
    indirect=True,
)
def test_create_new_item(fs_side: FilesystemSide):
    root = fs_side.filesystem_root
    os.chdir(root)

    all_items_before_addition = fs_side.get_all_items()
    prev_len = len(all_items_before_addition)

    # create a new FilesystemFile
    # By default, the item is created on disk automatically at this stage
    title = "the title"
    contents = "Kalimera!"
    new_item = FilesystemFile(path=title)
    new_item.contents = contents
    new_id = new_item.id
    assert new_id is not None

    # add the item to the side
    fs_side.add_item(new_item)

    # get the newly created item - make sure that its the same item as returned by
    # get_all_items()
    all_items_after_addition = fs_side.get_all_items()
    assert len(all_items_after_addition) == prev_len + 1
    fs_file = [item for item in all_items_after_addition if item.id == new_id][0]
    fs_file2 = fs_side.get_item(item_id=new_id)
    assert fs_file == fs_file2


def test_update_item(fs_side_with_existing_items: FilesystemSide):
    fs_side = fs_side_with_existing_items
    item = fs_side.get_all_items()[0]
    id_ = item.id
    assert id_ is not None

    new_contents = f"{item.contents} and some new content"
    new_title = "Some other title"
    item.contents = new_contents
    item.title = new_title
    fs_side.update_item(item_id=id_, **item)
    updated_item = fs_side.get_item(item_id=id_)
    assert updated_item is not None

    assert updated_item.contents == new_contents
    assert updated_item.title == new_title


def test_delete_item(fs_side_with_existing_items: FilesystemSide):
    fs_side = fs_side_with_existing_items
    prev_all_items = fs_side.get_all_items()
    item0, item1 = (item for item in prev_all_items[:2])
    id0 = item0.id
    id1 = item1.id
    assert id0 is not None
    assert id1 is not None
    prev_len = len(prev_all_items)

    # do some deletions
    fs_side.delete_single_item(item_id=id0)
    fs_side.delete_single_item(item_id=id1)
    curr_all_items = fs_side.get_all_items()
    curr_len = len(curr_all_items)
    assert curr_len == prev_len - 2

    # make sure the items have been deleted
    assert not item0._path.exists()
    assert not item1._path.exists()

    # this should be a nop
    fs_side.finish()


def test_items_are_identical(fs_side_with_existing_items: FilesystemSide):
    fs_side = fs_side_with_existing_items
    all_items = fs_side.get_all_items()
    item0, item1 = (item for item in all_items[:2])

    assert fs_side.items_are_identical(item0, item0)
    assert not fs_side.items_are_identical(item0, item1)

    item0.contents = item1.contents
    assert fs_side.items_are_identical(item0, item1, ignore_keys=["title", "id"])


def test_get_all_items(fs_side_with_existing_items: FilesystemSide):
    fs_side = fs_side_with_existing_items
    fs_files: Sequence[FilesystemFile] = fs_side.get_all_items()
    assert len(fs_files) == 10
    for fs_file in fs_files:
        # contents should be something like "Some content for file3"
        # title should be file3
        assert fs_file.title in fs_file.contents
        assert fs_file.id is not None


def test_item_not_in_cache(fs_side_with_existing_items: FilesystemSide):
    # create a new FilesystemFile in the root of this side, but don't register it. Make sure
    # that `get_item()` can find it.
    fs_side = fs_side_with_existing_items
    root = fs_side.filesystem_root
    fs_file = FilesystemFile(path=root / "kalimera")
    fs_file.contents = "some contents"
    fs_file.flush()
    assert fs_file.id is not None

    fs_file_returned = fs_side.get_item(item_id=fs_file.id)
    assert fs_file_returned is not None
    assert fs_file_returned.title == fs_file.title
    assert fs_file_returned.contents == fs_file.contents
    assert fs_file_returned.id == fs_file.id
