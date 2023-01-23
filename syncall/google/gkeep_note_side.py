from typing import Optional, Sequence, Set

from gkeepapi.node import Label, Note, TopLevelNode
from item_synchronizer.types import ID
from loguru import logger

from syncall.concrete_item import ConcreteItem
from syncall.google.gkeep_note import GKeepNote
from syncall.google.gkeep_side import GKeepSide


class GKeepNoteSide(GKeepSide):
    """Create, update, delete notes on the Google Keep side."""

    @classmethod
    def id_key(cls) -> str:
        return "id"

    @classmethod
    def summary_key(cls) -> str:
        return "title"

    @classmethod
    def last_modification_key(cls) -> str:
        return "last_modified_date"

    def __init__(
        self,
        gkeep_labels: Sequence[str] = tuple(),
        gkeep_ignore_labels: Sequence[str] = tuple(),
        **kargs,
    ) -> None:
        super().__init__(name="GKeep", fullname="Google Keep Notes", **kargs)
        self._gkeep_labels_strs = gkeep_labels or []
        self._gkeep_labels: Set[Label] = set()
        self._gkeep_ignore_labels_strs = gkeep_ignore_labels or []
        self._gkeep_ignore_labels: Set[Label] = set()

    def start(self):
        super().start()

        # TODO Test this
        # Label management --------------------------------------------------------------------
        # Create given labels if they don't already exist,
        # Get the concrete classes from strings
        # Do the above for both the labels and the ignore_labels
        for container, labels_str in (
            (self._gkeep_labels, self._gkeep_labels_strs),
            (self._gkeep_ignore_labels, self._gkeep_ignore_labels_strs),
        ):
            for label_str in labels_str:
                label = self._get_label_by_name(label_str)
                if label is None:
                    logger.debug(f"Creating new label -> {label_str}...")
                    container.add(self._keep.createLabel(label_str))
                else:
                    logger.debug(f"Using existing label -> {label_str}...")
                    self._gkeep_labels.add(label)

    def get_all_items(self, **kargs) -> Sequence[GKeepNote]:
        def note_contains_labels(node: TopLevelNode, labels: Set[Label]) -> bool:
            return labels.issubset(node.labels.all())

        def note_does_not_contain_labels(node: TopLevelNode, labels: Set[Label]) -> bool:
            return labels.isdisjoint(node.labels.all())

        def node_is_of_type_note(node: TopLevelNode) -> bool:
            return isinstance(node, Note)

        matching: Sequence[Note] = list(
            self._keep.find(
                func=lambda node: note_contains_labels(node, self._gkeep_labels)
                and note_does_not_contain_labels(node, self._gkeep_ignore_labels)
                and node_is_of_type_note(node)
                and not node.deleted
                and not node.archived
            )
        )

        return tuple(GKeepNote.from_gkeep_note(m) for m in matching)

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[GKeepNote]:
        for item in self.get_all_items():
            if item.id == item_id:
                return item

    def _get_item_by_id(self, item_id: ID) -> GKeepNote:
        item = self.get_item(item_id=item_id)
        if item is None:
            raise RuntimeError(f"Requested item {item_id} but that item cannot be found")
        return item

    def delete_single_item(self, item_id: ID) -> None:
        item = self._get_item_by_id(item_id=item_id)
        item.delete()

    def update_item(self, item_id: ID, **updated_properties):
        if not {"plaintext", "title"}.issubset(updated_properties.keys()):
            logger.warning(
                f"Invalid changes provided to GKeepNoteSide -> {updated_properties}"
            )
            return
        new_plaintext = updated_properties["plaintext"]
        new_title = updated_properties["title"]

        item = self._get_item_by_id(item_id=item_id)
        item.plaintext = new_plaintext
        item.title = new_title

    def add_item(self, item: GKeepNote) -> GKeepNote:
        new_item = self._keep.createNote(item.title, text=item.plaintext)
        for label in self._gkeep_labels:
            new_item.labels.add(label)
        return GKeepNote.from_gkeep_note(new_item)

    @classmethod
    def items_are_identical(
        cls, item1: ConcreteItem, item2: ConcreteItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = [cls.last_modification_key()]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)
