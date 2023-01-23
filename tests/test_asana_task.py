import datetime

from bubop import format_datetime_tz, parse_datetime

from syncall.asana.asana_task import AsanaTask
from syncall.types import AsanaRawTask

from .generic_test_case import GenericTestCase


class TestAsanaTask(GenericTestCase):
    """Test AsanaTask."""

    BASE_VALID_RAW_TASK = {
        "completed": False,
        "completed_at": None,
        "created_at": "2022-07-10T20:42:00Z",
        "due_at": None,
        "due_on": None,
        "gid": 123456789012345,
        "modified_at": "2022-07-10T20:43:00Z",
        "name": "First Asana Task",
    }

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(TestAsanaTask, self).setUp()

    def test_from_raw(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        for key in ["completed", "gid", "name"]:
            self.assertEqual(asana_task[key], valid_raw_task[key])

    def test_from_raw_task_asserts_keys(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        AsanaTask.from_raw_task(valid_raw_task)

        for key in AsanaTask._key_names:
            copy = valid_raw_task.copy()
            copy.pop(key, None)

            with self.assertRaises(AssertionError):
                AsanaTask.from_raw_task(copy)

    def test_from_raw_task_parses_date_and_datetime_fields(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        for key in ["created_at", "modified_at"]:
            self.assertIsInstance(asana_task[key], datetime.datetime)
            self.assertEqual(asana_task[key], parse_datetime(valid_raw_task[key]))

        for key in ["completed_at", "due_at"]:
            self.assertIsNone(asana_task[key])
            valid_raw_task[key] = "2022-07-10T20:55:00Z"
            asana_task = AsanaTask.from_raw_task(valid_raw_task)
            self.assertIsInstance(asana_task[key], datetime.datetime)
            self.assertEqual(asana_task[key], parse_datetime(valid_raw_task[key]))

        valid_raw_task["due_on"] = "2022-07-10"
        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        self.assertIsInstance(asana_task.due_on, datetime.date)
        self.assertEqual(
            asana_task.due_on, datetime.date.fromisoformat(valid_raw_task["due_on"])
        )

    def test_to_raw_task(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        asana_task = AsanaTask.from_raw_task(valid_raw_task)
        raw_task = asana_task.to_raw_task()

        for key in ["completed", "gid", "name"]:
            self.assertEqual(raw_task[key], asana_task[key])

        for key in ["created_at", "modified_at"]:
            self.assertEqual(raw_task[key], asana_task[key].isoformat(timespec="milliseconds"))

        for key in ["completed_at", "due_at", "due_on"]:
            kwargs = {}

            self.assertIsNone(raw_task[key])

            if key == "due_on":
                valid_raw_task[key] = "2022-07-10"
            else:
                kwargs["timespec"] = "milliseconds"
                valid_raw_task[key] = "2022-07-10T21:25:00Z"

            asana_task = AsanaTask.from_raw_task(valid_raw_task)

            raw_task = asana_task.to_raw_task()
            self.assertIsNotNone(raw_task[key])

            self.assertEqual(raw_task[key], asana_task[key].isoformat(**kwargs))
