from pathlib import Path
from typing import Optional


class AttributeNotSetError(BaseException):
    """
    Exception raised an attribute (e.g., on a file) has not been set as expected.
    """

    def __init__(self, attr_name: str, path: Optional[Path] = None):
        s = f"Attribute {attr_name} has not been set"
        if path is not None:
            s += f" for file {path}"

        super().__init__(s)
