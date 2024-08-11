import os
from pathlib import Path

from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide

from .generic_test_case import GenericTestCase


class TestTW(GenericTestCase):
    """Test TaskWarriorSide methods."""

    def setUp(self):
        super().setUp()

        # Make sure we're in the test directory for these tests
        os.chdir(str(Path(__file__).parent))
        self.tw_side = TaskWarriorSide(config_file_override=Path("test.taskrc"))

    def test_get_items(self):
        items = self.tw_side.get_all_items()

        # assert on the status
        assert all((i["status"] == "completed" or i["status"] == "pending") for i in items)

        # must be sorted by ID by default
        ids = [i["id"] for i in items]  # type: ignore
        assert ids == sorted(ids)
