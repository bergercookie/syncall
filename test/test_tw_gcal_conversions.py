#!/usr/bin/env python3

from taskw_gcal_sync.TWGCalAggregator import TWGCalAggregator
from .GenericTestCase import GenericTestCase

import unittest
import yaml
from pathlib import Path


class TestConversions(GenericTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        self.maxDiff = None
        pass

    def load_sample_items(self):
        with open(Path(GenericTestCase.DATA_FILES_PATH, 'sample_items.yaml'),
                  'r') as fname:
            conts = yaml.load(fname)

        self.gcal_item = conts['gcal_item']
        self.tw_item = conts['tw_item']

        self.gcal_item_expected = conts['gcal_item_expected']
        self.tw_item_expected = conts['tw_item_expected']

    def test_tw_gcal_basic_convert(self):
        """Basic TW -> GCal conversion."""
        self.load_sample_items()
        gcal_item_out = TWGCalAggregator.convert_tw_to_gcal(self.tw_item)
        self.assertDictEqual(gcal_item_out, self.gcal_item_expected)

    def test_gcal_tw_basic_convert(self):
        """Basic GCal -> TW conversion."""
        self.load_sample_items()
        tw_item_out = TWGCalAggregator.convert_gcal_to_tw(self.gcal_item)
        self.assertDictEqual(tw_item_out, self.tw_item_expected)


if __name__ == "__main__":
    unittest.main()
