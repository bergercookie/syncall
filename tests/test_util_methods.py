import os
from pathlib import Path

from syncall.taskwarrior.taskwarrior_side import TaskWarriorSide

from .generic_test_case import GenericTestCase


class TestTW(GenericTestCase):
    """Test TaskWarriorSide methods."""

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(TestTW, self).setUp()

        # Make sure we're in the test directory for these tests
        os.chdir(str(Path(__file__).parent))
        self.tw_side = TaskWarriorSide(config_file=Path("test.taskrc"))

    def test_get_items(self):
        items = self.tw_side.get_all_items()

        # assert on the status
        self.assertTrue(
            all((i["status"] == "completed" or i["status"] == "pending") for i in items)
        )

        # must be sorted by ID by default
        ids = [i["id"] for i in items]  # type: ignore
        self.assertListEqual(ids, sorted(ids))
        del items, ids
