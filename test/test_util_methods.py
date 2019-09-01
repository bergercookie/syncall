#!/usr/bin/env python3

from taskw_gcal_sync.TaskWarriorSide import TaskWarriorSide
from .GenericTestCase import GenericTestCase

from pathlib import Path
import os
import unittest
import yaml


class TestTW(GenericTestCase):
    """Test TaskWarriorSide methods"""
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(TestTW, self).setUp()

        # Make sure we're in the test directory for these tests
        os.chdir(str(Path(__file__).parent))
        self.tw_side = TaskWarriorSide(config_filename="test.taskrc")

    def test_get_items(self):
        items = self.tw_side.get_all_items()

        # assert on the status
        self.assertTrue(all([(i['status'] == 'completed' or
                              i['status'] == 'pending') for i in items]))

        # must be sorted by ID by default
        ids = [i['id'] for i in items]
        self.assertListEqual(ids, sorted(ids))
        del items, ids

        # test urgency ordering
        items = self.tw_side.get_all_items(order_by='urgency',
                                           use_ascending_order=False)
        urgencies = [i['urgency'] for i in items]
        self.assertListEqual(urgencies, sorted(urgencies, reverse=True))

        # test description alphabetical ordering
        items = self.tw_side.get_all_items(order_by='description',
                                           use_ascending_order=True)
        descs = [i['description'] for i in items]
        self.assertListEqual(descs, sorted(descs))


class TestGCal(GenericTestCase):
    # TODO
    """Test GCalSide methods"""
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(TestGCal, self).setUp()


if __name__ == "__main__":
    unittest.main()
