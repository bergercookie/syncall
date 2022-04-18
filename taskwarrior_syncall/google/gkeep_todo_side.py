from typing import Optional, Sequence

from bubop import AuthenticationError, logger
from gkeepapi import Keep
from gkeepapi.node import Label
from gkeepapi.node import List as GKeepList
from gkeepapi.node import TopLevelNode
from item_synchronizer.types import ID

from taskwarrior_syncall.google.gkeep_todo_item import GKeepTodoItem
from taskwarrior_syncall.sync_side import SyncSide


class GKeepTodoSide(SyncSide):
    """Integration for managing the checkboxes of a Google Keep note.

    Currently not using the official Google API since it's enterprise only, but using
    https://github.com/kiwiz/gkeepapi instead
    """

    ID_KEY = "id"
    SUMMARY_KEY = "plaintext"

    def __init__(
        self,
        note_title: str,
        gkeep_user: str,
        gkeep_passwd: str,
        notes_label: Optional[str] = None,
    ):
        """
        Initialise The GKeepTodoSide.

        :param note_title: Title of the note whose items will be synchronized with Taskwarrior.
        :param gkeep_user: Username to use for authenticating with Google Keep
        :param gkeep_passwd: Password to use for authenticating with Google Keep
        :param notes_label: Add this label to all the notes that this instance touches
        """
        super().__init__(
            name="GKeep",
            fullname="Google Keep",
        )
        self._note_title = note_title
        self._gkeep_user = gkeep_user
        self._gkeep_passwd = gkeep_passwd
        self._notes_label_str = notes_label
        self._notes_label: Optional[Label] = None
        self._keep: Keep
        self._note: GKeepList

        self._pending_items: Sequence[GKeepTodoItem] = []

    def start(self):
        logger.debug("Connecting to Google Keep...")
        self._keep = Keep()
        success = self._keep.login(self._gkeep_user, self._gkeep_passwd)
        if not success:
            raise AuthenticationError(appname="Google Keep")

        logger.debug("Connected to Google Keep.")

        # create a new label if one was provided / use existing one -----------------------
        if self._notes_label_str is not None:
            label = self._get_label_by_name(self._notes_label_str)
            if label is None:
                logger.debug(f"Creating new label -> {self._notes_label_str}...")
                self._notes_label = self._keep.createLabel(self._notes_label_str)
            else:
                logger.debug(f"Using existing label -> {self._notes_label_str}...")
                self._notes_label = label

        # Find the note - act accordingly if it doesn't exist ---------------------------------
        # - If the note is in the trash or is deleted throw an error
        # - If the note is found but is of Note (instead of List) type, then an error is
        #   thrown and the user is instructed to enable the checkboxes.
        # - If there are multiple matching note names, throw an error
        # - If the note is not found by its name it will be created
        logger.debug(f'Looking for notes with a matching title - "{self._note_title}"')
        notes_w_matching_title: Sequence[TopLevelNode] = list(
            self._keep.find(func=lambda x: x.title == self._note_title)
        )

        # found matching note(s)
        if len(notes_w_matching_title):
            logger.debug(f"Found {len(notes_w_matching_title)} notes with matching title...")
            non_deleted_archived_notes = [
                note
                for note in notes_w_matching_title
                if not note.deleted and not note.archived
            ]

            # all are deleted/archived - error
            if not non_deleted_archived_notes:
                raise RuntimeError(
                    "Found note(s) with a matching title but they are deleted/archived. Can't"
                    " proceed. Please either restore/unarchive them or specify a new note to"
                    " use..."
                )
            len_non_deleted_archived_notes = len(non_deleted_archived_notes)

            active_notes_tlist = [
                note for note in non_deleted_archived_notes if isinstance(note, GKeepList)
            ]

            # no notes of type List found - error
            len_active_notes_tlist = len(active_notes_tlist)
            if not len_active_notes_tlist:
                raise RuntimeError(
                    f'Found {len_non_deleted_archived_notes} note(s) but none of type "List".'
                    ' Make sure to toggle the option "Show checkboxes" in the note that you'
                    " intend to use for the synchronization"
                )

            # more than one note found - ambiguous
            if len_active_notes_tlist != 1:
                raise RuntimeError(
                    f"Found {len_active_notes_tlist} candidate notes. This is ambiguous."
                    " Either rename the note(s) accordingly or specify another title."
                )

            self._note = active_notes_tlist[0]

            # assign label to note if it doesn't have it already
            if self._notes_label is not None and not self._note_has_label(
                self._note, self._notes_label
            ):
                logger.debug(f"Assigning label {self._notes_label_str} to note...")
                self._note.labels.add(self._notes_label)
        else:
            # create new note -----------------------------------------------------------------
            logger.info(
                "Couldn't find note with the given title - Creating it from scratch..."
            )
            self._note = self._create_note(self._note_title)

    def _note_has_label(self, note: TopLevelNode, label: Label) -> bool:
        """True if the given Google Keep note has the given label."""
        for la in note.labels.all():
            if label == la:
                return True

        return False

    def _note_has_label_str(self, note: TopLevelNode, label_str: str) -> bool:
        """True if the given Google Keep note has the given label."""
        for la in note.labels.all():
            if label_str == la.name:
                return True

        return False

    def finish(self):
        logger.info("Flushing data to remote Google Keep...")
        self._keep.sync()

    def _get_label_by_name(self, label: str) -> Optional[Label]:
        for la in self._keep.labels():
            if la.name == label:
                return la

    def _create_note(self, note_title: str) -> GKeepList:
        """Create a new note (list of items) in Google Keep.

        Applies the predefined label to the note - if one was provided during initialization.
        """
        li = self._keep.createList(note_title)
        if self._notes_label is not None:
            li.labels.add(self._notes_label)

        return li

    def get_all_items(self, **kargs) -> Sequence[GKeepTodoItem]:
        """Get all the todo entries of the Note in use."""
        return tuple(
            GKeepTodoItem.from_gkeep_list_item(child) for child in self._note.children
        )

    def get_item(self, item_id: str, use_cached: bool = True) -> Optional[GKeepTodoItem]:
        item = self._note.get(item_id)
        if item is None:
            logger.warning(f"Couldn't fetch Google Keep item with id {item_id}.")
            return None
        return GKeepTodoItem.from_gkeep_list_item(item)

    def update_item(self, item_id: ID, **updated_properties):
        if not {"plaintext", "is_checked"}.issubset(updated_properties.keys()):
            logger.warning(f"Invalid changes provided to GKeepSide -> {updated_properties}")
            return
        new_plaintext = updated_properties["plaintext"]
        new_is_checked = updated_properties["is_checked"]

        item = self._get_item_by_id(item_id=item_id)
        item.plaintext = new_plaintext
        item.is_checked = new_is_checked

    def add_item(self, item: GKeepTodoItem) -> GKeepTodoItem:
        new_item = self._note.add(text=item.plaintext, checked=item.is_checked)
        return GKeepTodoItem.from_gkeep_list_item(new_item)

    def delete_single_item(self, item_id: ID) -> None:
        item = self._get_item_by_id(item_id=item_id)
        item.delete()

    def _get_item_by_id(self, item_id: ID) -> GKeepTodoItem:
        item = self._note.get(item_id)
        if item is None:
            raise RuntimeError(
                f"Requested the deletion of item {item_id} but that item cannot be found"
            )

        return GKeepTodoItem.from_gkeep_list_item(item)

    @classmethod
    def id_key(cls) -> str:
        return cls.ID_KEY

    @classmethod
    def summary_key(cls) -> str:
        return cls.SUMMARY_KEY

    @classmethod
    def last_modification_key(cls) -> str:
        return "last_modified_date"

    @classmethod
    def items_are_identical(
        cls, item1: GKeepTodoItem, item2: GKeepTodoItem, ignore_keys: Sequence[str] = []
    ) -> bool:
        ignore_keys_ = ["last_edited_time"]
        ignore_keys_.extend(ignore_keys)
        return item1.compare(item2, ignore_keys=ignore_keys_)
