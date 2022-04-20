from pathlib import Path

import pytest

from syncall.filesystem.filesystem_file import FilesystemFile
from syncall.filesystem.filesystem_side import FilesystemSide


@pytest.fixture
def fs_side(request: pytest.FixtureRequest) -> dict:
    """Fixture to parametrize on."""
    param = request.param  # type: ignore
    return request.getfixturevalue(param)


@pytest.fixture
def fs_file_default_fname() -> str:
    return "file.txt"


@pytest.fixture
def fs_file_default_name() -> str:
    return "file"


@pytest.fixture
def tmpdir_path(tmpdir) -> Path:
    return Path(tmpdir)


@pytest.fixture
def non_existent_python_path(tmpdir_path, fs_file_default_fname) -> Path:
    return tmpdir_path / fs_file_default_fname


@pytest.fixture
def fs_file_empty(tmpdir_path, fs_file_default_fname) -> FilesystemFile:
    fs = FilesystemFile(tmpdir_path / fs_file_default_fname)

    return fs


@pytest.fixture
def python_path_with_content(tmpdir_path, fs_file_default_fname) -> Path:
    path = tmpdir_path / fs_file_default_fname
    path.write_text(
        """Here is some
multi-line text
with unicode 🚀😄 characters.
"""
    )
    return path


@pytest.fixture
def fs_file_with_content(python_path_with_content: Path) -> FilesystemFile:
    fs = FilesystemFile(python_path_with_content)

    return fs


def _create_fs_side(filesystem_root: str):
    return FilesystemSide(filesystem_root=Path(filesystem_root), filename_extension=".txt")


@pytest.fixture
def fs_side_no_items(tmpdir) -> FilesystemSide:
    return _create_fs_side(filesystem_root=tmpdir)


@pytest.fixture
def fs_side_with_existing_items(tmpdir) -> FilesystemSide:
    dir_ = Path(tmpdir)
    for i in range(10):
        with FilesystemFile(path=f"file{i}", flush_on_instantiation=False) as fs:
            fs.contents = f"Some content for file{i}"
            fs.root = dir_
            fs.flush()

    return _create_fs_side(filesystem_root=tmpdir)
