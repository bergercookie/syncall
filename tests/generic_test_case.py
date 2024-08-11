"""Test the basic conversions between Google Calendar and TaskWarrior items."""

import unittest
from pathlib import Path


class GenericTestCase(unittest.TestCase):
    """Generic unittest class for the project."""

    DATA_FILES_PATH = Path(__file__).parent / "test_data"

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.maxDiff = None
