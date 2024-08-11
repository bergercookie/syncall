from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class AttributeNotSetError(BaseException):
    """Exception raised an attribute (e.g., on a file) has not been set as expected."""

    def __init__(self, attr_name: str, path: Path | None = None):
        """Initialize the exception."""
        s = f"Attribute {attr_name} has not been set"
        if path is not None:
            s += f" for file {path}"

        super().__init__(s)
