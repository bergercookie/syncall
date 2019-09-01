"""
Test the basic conversions between Google Calendar and TaskWarrior items.
"""

import unittest
import os


class GenericTestCase(unittest.TestCase):
    """

    :ivar DATA_FILES_PATH: Path to the directory holding data files for testing.
    """
    DATA_FILES_PATH = os.path.join(os.path.dirname(__file__),
                                   "test_data")

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.maxDiff = None
