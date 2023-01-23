from dataclasses import dataclass
from typing import Optional, Sequence

from syncall.sync_side import SyncSide


@dataclass
class SideHelper:
    """A helper class holding high-level info about the SyncSide at hand."""

    # Name of the side this helper corresponds to
    name: str
    id_key: str
    summary_key: str
    # Handy way to refer to the counterpart side
    other: Optional["SideHelper"] = None
    ignore_keys: Sequence[str] = tuple()

    def __str__(self):
        return str(self.name)

    @classmethod
    def from_side(cls, side: SyncSide) -> "SideHelper":
        return cls(
            name=side.name,
            id_key=side.id_key(),
            summary_key=side.summary_key(),
        )
