import sys

from pytermgui.widgets.button import Button

import cluecoins.cli as cli
from cluecoins.sync_manager import SyncManager


class Actions:
    def __init__(self, db_path: str | None) -> None:
        self._db = db_path
        self._sync = SyncManager()

    @property
    def db(self) -> str:
        if self._db is None:
            self._db = self._sync.prepare_local_db()
        return self._db

    def start_convert(self, base_currency: str) -> None:

        cli._convert(base_currency, self._db)

    def start_archive_account(self, button: Button, account_name: str) -> None:

        cli._archive(account_name, self._db)

    def start_unarchive_account(self, button: Button | None, account_name: str) -> None:

        cli._unarchive(account_name, self._db)

    def close_session(self) -> None:
        """Run app activity:
                default: opening an app on the phone

        Close terminal interface.
        """

        if not self._db:
            # FIXME: hardcode
            self._sync.push_changes_to_app('.ui.activities.main.MainActivity')
        sys.exit(0)
