"""Filesystem <-> Google Keep conversion functions"""

from pathlib import Path

from bubop.string import get_random_string

from syncall.filesystem.filesystem_file import FilesystemFile
from syncall.google.gkeep_note import GKeepNote


def convert_filesystem_file_to_gkeep_note(filesystem_file: FilesystemFile) -> GKeepNote:
    return GKeepNote(plaintext=filesystem_file.contents, title=filesystem_file.title)


def convert_gkeep_note_to_filesystem_file(
    gkeep_note: GKeepNote,
    filename_extension=FilesystemFile.default_ext,
    filesystem_root: Path = Path("."),
) -> FilesystemFile:
    """
    GKeep Note -> Filesystemm File

    :param gkeep_note: The note to convert
    :param filename_extension: The extension to use for the created file.
    :return: The newly created FilesystemFile
    """

    # determine note title with the following order
    # 1. Original GKeep note title (unless empty)
    # 2. First line of GKeep note (unless empty file)
    # 3. Random string
    if gkeep_note.title:
        note_title = gkeep_note.title
    elif gkeep_note.plaintext:
        note_title = gkeep_note.plaintext.splitlines()[0]
    else:
        note_title = get_random_string()

    filename_extension = filename_extension.lstrip(".")

    fs = FilesystemFile(path=filesystem_root / f"{note_title}.{filename_extension}")
    fs.contents = gkeep_note.plaintext
    return fs
