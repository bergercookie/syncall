import datetime
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from bubop import parse_datetime

from syncall.types import AsanaGID, AsanaRawTask


@dataclass
class AsanaTask(Mapping):
    completed: bool
    completed_at: datetime.datetime
    created_at: datetime.datetime
    due_at: datetime.datetime
    due_on: datetime.date
    name: str
    modified_at: datetime.datetime
    gid: Optional[AsanaGID] = None

    _key_names = {
        "completed",
        "completed_at",
        "created_at",
        "due_at",
        "due_on",
        "gid",
        "name",
        "modified_at",
    }

    def __getitem__(self, key) -> Any:
        return getattr(self, key)

    def __iter__(self):
        for k in self._key_names:
            yield k

    def __len__(self):
        return len(self._key_names)

    @classmethod
    def from_raw_task(cls, raw_task: AsanaRawTask) -> "AsanaTask":
        assert "completed" in raw_task
        assert "completed_at" in raw_task
        assert "created_at" in raw_task
        assert "due_at" in raw_task
        assert "due_on" in raw_task
        assert "gid" in raw_task
        assert "modified_at" in raw_task
        assert "name" in raw_task

        completed = raw_task["completed"]
        completed_at = None
        if raw_task["completed_at"] is not None:
            completed_at = parse_datetime(raw_task["completed_at"])
        created_at = parse_datetime(raw_task["created_at"])
        due_at = None
        if raw_task["due_at"] is not None:
            due_at = parse_datetime(raw_task["due_at"])
        due_on = None
        if raw_task["due_on"] is not None:
            due_on = datetime.date.fromisoformat(raw_task["due_on"])
        gid = raw_task["gid"]
        modified_at = parse_datetime(raw_task["modified_at"])
        name = raw_task["name"]

        return AsanaTask(
            completed=completed,
            completed_at=completed_at,
            created_at=created_at,
            due_at=due_at,
            due_on=due_on,
            gid=gid,
            modified_at=modified_at,
            name=name,
        )

    def to_raw_task(self) -> AsanaRawTask:
        raw_task = {
            "completed": self.completed,
            "created_at": self.created_at.isoformat(timespec="milliseconds"),
            "gid": self.gid,
            "name": self.name,
        }

        if self.completed_at is not None:
            raw_task["completed_at"] = self.completed_at.isoformat(timespec="milliseconds")
        else:
            raw_task["completed_at"] = None

        if self.due_at is not None:
            raw_task["due_at"] = self.due_at.isoformat(timespec="milliseconds")
        else:
            raw_task["due_at"] = None

        if self.due_on is not None:
            raw_task["due_on"] = self.due_on.isoformat()
        else:
            raw_task["due_on"] = None

        if self.modified_at is not None:
            raw_task["modified_at"] = self.modified_at.isoformat(timespec="milliseconds")
        else:
            raw_task["modified_at"] = None

        return raw_task
