import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping

@dataclass
class CattrTask(Mapping):
    """Represents a Cattr Task."""
    start_date: str
    due_date 	: str
    users:list[int]
    project_phase_id: int
    project_id:int
    task_name:str
    description :str
    important:bool
    priority_id :int
    status_id :int
    ##
    url: str
    project_name: str
    id:int
    assigned_by:int
    created_at:str
    updated_at:str
    deleted_at:str
    relative_position:int
    estimate:int
    _key_names: frozenset[str]=frozenset({
                "start_date",
                "due_date",
                "users",
                "project_phase_id",
                "project_id",
                "task_name",
                "description",
                "important",
                "priority_id",
                "status_id",
                "url",
                "project_name",
                "id",
                "assigned_by",
                "created_at",
                "updated_at",
                "deleted_at",
                "relative_position",
                "estimate",
        },)

    def __getitem__(self, key) -> Any:  # noqa: ANN401
        return getattr(self, key)

    def __iter__(self):
        yield from self._key_names

    def __len__(self):
        return len(self._key_names)
    @classmethod
    def from_json(cls,jsn): # -> CattrTask:
        return CattrTask(
                start_date = jsn.get("start_date",datetime.datetime.today()),
                due_date = jsn.get("due_date",datetime.datetime.today()),
                users = jsn.get("users",None),
                project_phase_id = jsn.get("project_phase_id",None),
                project_id = jsn.get("project_id",None),
                task_name = jsn.get("task_name",None),
                description = jsn.get("description","todo"),
                important = jsn.get("important",None),
                priority_id = jsn.get("priority_id",None),
                status_id = jsn.get("status_id",None),
                url = jsn.get("url",None),
                project_name = jsn.get("project_name","default"),
                id = jsn.get("id",None),
                assigned_by = jsn.get("assigned_by",None),
                created_at = jsn.get("created_at",None),
                updated_at = jsn.get("updated_at",None),
                deleted_at = jsn.get("deleted_at",None),
                relative_position = jsn.get("relative_position",None),
                estimate = jsn.get("estimate",None),
                )
