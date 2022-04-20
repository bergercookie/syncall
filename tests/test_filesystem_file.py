from pathlib import Path

import pytest
import xattr

from syncall.filesystem.filesystem_file import FilesystemFile

from .conftest_helpers import fixture_false, fixture_true


# helper fixtures -----------------------------------------------------------------------------
@pytest.fixture
def flush_on_instantiation(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def fs_file_path(request):
    return request.getfixturevalue(request.param)


# tests ---------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "fs_file_path,flush_on_instantiation",
    [
        ("python_path_with_content", "fixture_true"),
        ("python_path_with_content", "fixture_false"),
    ],
    indirect=True,
)
def test_fs_file_flush_attrs(fs_file_path: Path, flush_on_instantiation: bool):
    """
    Make sure that extended attributes of the FilesystemFile is only written when
    we actually .flush() it.
    """
    p = fs_file_path
    fs_file = FilesystemFile(path=p, flush_on_instantiation=flush_on_instantiation)

    x = xattr.xattr(p)

    assert fs_file.id is not None
    if flush_on_instantiation:
        assert x.list()
    else:
        assert not x.list()

    # flush -----------------------------------------------------------------------------------
    fs_file.flush()

    assert len(x.list()) == 1
    assert x.get(FilesystemFile._attr) is not None


def test_fs_file_flush_change_title_content(python_path_with_content: Path):
    """
    Make sure that title and content of the FilesystemFile is written when we actually .flush()
    it.
    """
    p = python_path_with_content
    path_contents = p.read_text()
    path_title = p.stem

    fs_file = FilesystemFile(path=p)
    assert fs_file.contents == path_contents
    assert fs_file.title == path_title
    assert fs_file.id != None

    # change contents and title
    new_contents = "New contents\nwith a bunch of lines\n🥳🥳🥳"
    new_title = "ένας νέος τίτλος"  # title uses unicode
    fs_file.contents = new_contents
    fs_file.title = new_title

    # flush -----------------------------------------------------------------------------------
    fs_file.flush()

    # test new title
    new_path = p.with_name(new_title).with_suffix(".txt")
    assert not p.exists()
    assert new_path.is_file()

    # test new contents
    assert new_path.read_text() == new_contents


def test_fs_file_dict_fns(non_existent_python_path: Path):
    fs_file = FilesystemFile(path=non_existent_python_path, flush_on_instantiation=False)
    assert set(("last_modified_date", "contents", "title", "id")).issubset(
        key for key in fs_file.keys()
    )

    assert fs_file["last_modified_date"].year == 1970
    assert fs_file["contents"] == ""
    assert fs_file["title"] == non_existent_python_path.stem
    assert fs_file["id"] is not None


def test_fs_file_delete(python_path_with_content: Path):
    """Verify that deletion happens on flush and not before it."""
    p = python_path_with_content
    fs = FilesystemFile(p)

    assert p.is_file()
    fs.delete()
    assert p.is_file()
    fs.flush()
    assert not p.exists()


def test_fs_file_open_twice(python_path_with_content: Path):
    new_content1 = "some other content"
    new_content2 = "some yet another content"
    p = python_path_with_content
    fs1 = FilesystemFile(p)
    fs1.contents = new_content1
    fs1.flush()
    assert p.read_text() == new_content1

    fs2 = FilesystemFile(p)
    fs2.contents = new_content2
    fs2.flush()
    assert p.read_text() == new_content2
