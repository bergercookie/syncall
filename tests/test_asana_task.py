from __future__ import annotations

import datetime
from typing import Any, ClassVar

import pytest
from bubop import parse_datetime
from syncall.asana.asana_task import AsanaTask

from .generic_test_case import GenericTestCase


class TestAsanaTask(GenericTestCase):
    """Test AsanaTask."""

    BASE_VALID_RAW_TASK: ClassVar[dict[str, Any]] = {
        "completed": False,
        "completed_at": None,
        "created_at": "2022-07-10T20:42:00Z",
        "due_at": None,
        "due_on": None,
        "gid": 123456789012345,
        "modified_at": "2022-07-10T20:43:00Z",
        "name": "First Asana Task",
    }

    def test_from_raw(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        for key in ["completed", "gid", "name"]:
            assert asana_task[key] == valid_raw_task[key]

    def test_from_raw_task_asserts_keys(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        AsanaTask.from_raw_task(valid_raw_task)

        for key in AsanaTask._key_names:
            copy = valid_raw_task.copy()
            copy.pop(key, None)

            with pytest.raises(AssertionError):
                AsanaTask.from_raw_task(copy)

    def test_from_raw_task_parses_date_and_datetime_fields(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()

        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        for key in ["created_at", "modified_at"]:
            assert isinstance(asana_task[key], datetime.datetime)
            assert asana_task[key] == parse_datetime(valid_raw_task[key])

        for key in ["completed_at", "due_at"]:
            assert asana_task[key] is None
            valid_raw_task[key] = "2022-07-10T20:55:00Z"
            asana_task = AsanaTask.from_raw_task(valid_raw_task)
            assert isinstance(asana_task[key], datetime.datetime)
            assert asana_task[key] == parse_datetime(valid_raw_task[key])

        valid_raw_task["due_on"] = "2022-07-10"
        asana_task = AsanaTask.from_raw_task(valid_raw_task)

        assert isinstance(asana_task.due_on, datetime.date)
        assert asana_task.due_on == datetime.date.fromisoformat(valid_raw_task["due_on"])

    def test_to_raw_task(self):
        valid_raw_task = self.BASE_VALID_RAW_TASK.copy()
        asana_task = AsanaTask.from_raw_task(valid_raw_task)
        raw_task = asana_task.to_raw_task()

        for key in ["completed", "gid", "name"]:
            assert raw_task[key] == asana_task[key]

        for key in ["created_at", "modified_at"]:
            assert raw_task[key] == asana_task[key].isoformat(timespec="milliseconds")

        for key in ["completed_at", "due_at", "due_on"]:
            kwargs = {}

            assert raw_task[key] is None

            if key == "due_on":
                valid_raw_task[key] = "2022-07-10"
            else:
                kwargs["timespec"] = "milliseconds"
                valid_raw_task[key] = "2022-07-10T21:25:00Z"

            asana_task = AsanaTask.from_raw_task(valid_raw_task)

            raw_task = asana_task.to_raw_task()
            assert raw_task[key] is not None

            assert raw_task[key] == asana_task[key].isoformat(**kwargs)
