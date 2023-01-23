from typing import Optional

from bubop import logger
from bubop.exceptions import AuthenticationError
from gkeepapi import Keep
from gkeepapi.exception import LoginException
from gkeepapi.node import Label
from gkeepapi.node import List as GKeepList
from gkeepapi.node import TopLevelNode

from syncall.sync_side import SyncSide


class GKeepSide(SyncSide):
    def __init__(
        self,
        gkeep_user: str,
        gkeep_passwd: Optional[str] = None,
        gkeep_token: Optional[str] = None,
        **kargs,
    ):
        self._keep: Keep
        self._gkeep_user = gkeep_user
        self._gkeep_passwd = gkeep_passwd
        self._gkeep_token = gkeep_token

        super().__init__(**kargs)

    def get_master_token(self) -> Optional[str]:
        """
        Return a master token. Use it to authenticate in place of a password on subsequent
        runs.
        """
        return self._gkeep_token

    def start(self):
        super().start()
        logger.debug("Connecting to Google Keep...")
        self._keep = Keep()

        try:
            self._keep.resume(self._gkeep_user, self._gkeep_token, state=None, sync=True)
            logger.info("Logged in using token")
        except LoginException:
            # We have a token and we couldn't log in using this token, thus it's invalid.
            if self._gkeep_token is not None:
                logger.debug("Invalid token, attempting login via username/password...")
            self._keep.login(self._gkeep_user, self._gkeep_passwd)
            logger.info("Logged in using username/password")

        # we're logged in, cache the token
        self._gkeep_token = self._keep.getMasterToken()

    def finish(self):
        logger.info("Flushing data to remote Google Keep...")
        self._keep.sync()

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

    def _get_label_by_name(self, label: str) -> Optional[Label]:
        for la in self._keep.labels():
            if la.name == label:
                return la

    def _create_list(self, title: str, label: Optional[Label] = None) -> GKeepList:
        """Create a new list of items in Google Keep.

        Applies the given label to the note - if one was provided
        """
        li = self._keep.createList(title)
        if label is not None:
            li.labels.add(label)

        return li
