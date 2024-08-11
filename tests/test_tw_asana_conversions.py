import yaml
from syncall.asana.asana_task import AsanaTask
from syncall.tw_asana_utils import convert_asana_to_tw, convert_tw_to_asana

from .generic_test_case import GenericTestCase


class TestTwAsanaConversions(GenericTestCase):
    """Test item conversions - TW <-> Asana."""

    def get_keys_to_match(self):
        return set(self.tw_item.keys()).intersection(
            ("description", "due", "modified", "status"),
        )

    def load_sample_items(self):
        with (GenericTestCase.DATA_FILES_PATH / "sample_items.yaml").open() as fname:
            conts = yaml.load(fname, Loader=yaml.Loader)  # noqa: S506

        self.asana_task = conts["asana_task"]
        self.tw_item_expected = conts["tw_item_expected"]

        self.tw_item = conts["tw_item"]
        self.asana_task_expected = conts["asana_task_expected"]

        self.tw_item_w_due = conts["tw_item_w_due"]

    def test_tw_asana_basic_convert(self):
        """Basic TW -> Asana conversion."""
        self.load_sample_items()
        asana_task_out = convert_tw_to_asana(self.tw_item)
        for key in AsanaTask._key_names:
            assert asana_task_out[key] == self.asana_task_expected[key], key

    def test_asana_tw_basic_convert(self):
        """Basic Asana -> TW conversion."""
        self.load_sample_items()
        tw_item_out = convert_asana_to_tw(self.asana_task)
        for key in self.get_keys_to_match():
            assert tw_item_out[key] == self.tw_item_expected[key]

    def test_tw_asana_n_back(self):
        """TW -> Asana -> TW conversion"""
        self.load_sample_items()
        tw_item_out = convert_asana_to_tw(convert_tw_to_asana(self.tw_item))

        for key in self.get_keys_to_match():
            if key in self.tw_item:
                assert key in tw_item_out
                assert self.tw_item[key] == tw_item_out[key]
            if key in tw_item_out:
                assert key in self.tw_item
                assert tw_item_out[key] == self.tw_item[key]

    def test_asana_tw_n_back_basic(self):
        """Test Asana -> TW -> Asana conversion."""
        self.load_sample_items()
        asana_task_out = convert_tw_to_asana(convert_asana_to_tw(self.asana_task))

        for key in [
            "completed",
            "completed_at",
            "created_at",
            "due_at",
            "modified_at",
            "name",
        ]:
            if key in self.asana_task:
                assert key in asana_task_out
                assert self.asana_task[key] == asana_task_out[key]
            if key in asana_task_out:
                assert key in self.asana_task
                assert asana_task_out[key] == self.asana_task[key]

    def test_tw_asana_sets_both_due_dates(self):
        """Test that due dates are set in both TW and Asana."""
        self.load_sample_items()

        assert "due" in self.tw_item_w_due
        assert self.tw_item_w_due is not None

        asana_task = convert_tw_to_asana(self.tw_item_w_due)

        assert "due_at" in asana_task
        assert asana_task["due_at"] == self.tw_item_w_due["due"]
        assert "due_on" in asana_task
        assert asana_task["due_on"] == asana_task["due_at"].date()
