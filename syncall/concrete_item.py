import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Iterator, Mapping, Optional, Sequence, Union

from bubop.time import is_same_datetime
from item_synchronizer.types import ID
from loguru import logger


class KeyType(Enum):
    String = auto()
    Date = auto()
    Boolean = auto()
    SeqOfStrings = auto()


@dataclass
class ItemKey:
    name: str
    type: KeyType

    def __hash__(self):
        return hash(f"{self.name},{self.type.name}")


class _ConcreteItemMeta(Mapping, ABC):
    pass


class ConcreteItem(_ConcreteItemMeta):
    """Type of the items passed around in the synchronization classes."""

    def __init__(self, keys: Sequence[ItemKey]):
        self._keys = set(keys)
        self._keys.add(ItemKey(name="id", type=KeyType.String))
        self._str_to_key: Mapping[str, ItemKey] = {key.name: key for key in self._keys}

    @property
    def id(self) -> Optional[ID]:
        return self._id()

    @abstractmethod
    def _id(self) -> Optional[str]:
        pass

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        for k in self._keys:
            yield k.name

    def __len__(self):
        return len(self._keys)

    def compare(
        self,
        other: "ConcreteItem",
        ignore_keys: Optional[Sequence[Union[ItemKey, str]]] = None,
    ) -> bool:
        """Compare two items, return True if they are considered equal, False otherwise.

        By default go through and check all the registerd keys.
        """
        if ignore_keys is None:
            ignore_keys = []

        # the ignore_keys should be given as a Sequence[ItemKey] but until then, whatever keys
        # come in, we convert them to ItemKey.
        ignore_keys_ = []
        for key in ignore_keys:
            if isinstance(key, str):
                ignore_keys_.append(self._str_to_key[key])
            else:
                ignore_keys_.append(key)

        keys_to_check = self._keys - set(ignore_keys_)

        for key in keys_to_check:
            if key.type is KeyType.Date:
                if not is_same_datetime(
                    self[key.name], other[key.name], tol=datetime.timedelta(minutes=10)
                ):
                    logger.opt(lazy=True).trace(
                        f"\n\nItems differ\n\nItem1\n\n{self}\n\nItem2\n\n{other}\n\nKey"
                        f" [{key.name}] is different - [{repr(self[key.name])}] |"
                        f" [{repr(other[key.name])}]"
                    )
                    return False
            else:
                if self[key.name] != other[key.name]:
                    logger.opt(lazy=True).trace(
                        f"Items differ [{key.name}]\n\n{self}\n\n{other}"
                    )
                    return False

        return True
