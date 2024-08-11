from __future__ import annotations

from typing import Any

import yaml
from syncall.tw_caldav_utils import convert_caldav_to_tw, convert_tw_to_caldav

from .generic_test_case import GenericTestCase


class TestConversions(GenericTestCase):
    """Test item conversions - TW <-> Caldav Calendar."""

    def load_sample_items(self):
        with (GenericTestCase.DATA_FILES_PATH / "sample_items.yaml").open() as fname:
            conts = yaml.load(fname, Loader=yaml.Loader)  # noqa: S506

        self.caldav_item = conts["caldav_item"]
        self.tw_item_expected = conts["tw_item_expected"]

        self.tw_item: dict[str, Any] = conts["tw_item"]
        self.tw_item_w_due = conts["tw_item_w_due"]
        self.caldav_item_expected = conts["caldav_item_expected"]
        self.caldav_item_w_date_expected = conts["caldav_item_w_date_expected"]

        self.caldav_item_w_date = conts["caldav_item_w_date"]
        self.tw_item_w_date_expected = conts["tw_item_w_date_expected"]

        # we don't care about this field yet.
        self.tw_item.pop("syncallduration")
        self.tw_item_expected.pop("syncallduration")

        self.tw_item_w_date_expected.pop("syncallduration")
        if "entry" in self.tw_item_w_date_expected:
            self.tw_item_w_date_expected.pop("entry")
        if "created" in self.tw_item_w_date_expected:
            self.tw_item_w_date_expected.pop("created")

    def test_tw_caldav_basic_convert(self):
        """Basic TW -> Caldav conversion."""
        self.load_sample_items()
        caldav_item_out = convert_tw_to_caldav(self.tw_item)
        caldav_item_out.pop("created", "")
        assert caldav_item_out == self.caldav_item_expected

    def test_tw_caldav_w_due_convert(self):
        """Basic TW (with 'due' subfield) -> Caldav conversion."""
        self.load_sample_items()
        caldav_item_out = convert_tw_to_caldav(self.tw_item_w_due)
        caldav_item_out.pop("created", "")
        assert caldav_item_out == self.caldav_item_w_date_expected

    def test_caldav_tw_basic_convert(self):
        """Basic Caldav -> TW conversion."""
        self.load_sample_items()
        tw_item_out = convert_caldav_to_tw(self.caldav_item)
        assert tw_item_out == self.tw_item_expected

    def test_caldav_tw_date_convert(self):
        """Caldav (with 'date' subfield) -> TW conversion."""
        self.load_sample_items()
        tw_item_out = convert_caldav_to_tw(self.caldav_item_w_date)
        assert tw_item_out == self.tw_item_w_date_expected

    def test_tw_caldav_n_back(self):
        """TW -> Caldav -> TW conversion."""
        self.load_sample_items()

        # UGLY - Rewrite how we do testing for caldav<>tw and gcal<>tw
        intermediate_caldav = convert_tw_to_caldav(self.tw_item)
        intermediate_caldav["priority"] = ""
        intermediate_caldav.pop("created", "")

        tw_item_out = convert_caldav_to_tw(intermediate_caldav)
        assert set(self.tw_item) ^ set(tw_item_out) == set({"id", "urgency", "entry"})

        intersection = set(self.tw_item) & set(tw_item_out)
        assert {i: self.tw_item[i] for i in intersection} == {
            i: tw_item_out[i] for i in intersection
        }

    def test_caldav_tw_n_back(self):
        """Caldav -> TW -> Caldav conversion."""
        self.load_sample_items()
        caldav_item_out = convert_tw_to_caldav(convert_caldav_to_tw(self.caldav_item))

        # UGLY - Rewrite how we do testing for caldav<>tw and gcal<>tw
        caldav_item_out["priority"] = ""
        assert set(self.caldav_item) ^ set(caldav_item_out) == {"id"}
