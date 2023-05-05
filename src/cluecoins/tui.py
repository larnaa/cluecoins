import sqlite3 as lite
import sys
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from pytermgui.enums import Overflow
from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Label
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.widgets.input_field import InputField
from pytermgui.window_manager.layouts import Layout
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

import cluecoins.actions as actions
from cluecoins.database import get_accounts_list
from cluecoins.sync_manager import SyncManager

PYTERMGUI_CONFIG = """
config:
    InputField:
        styles:
            prompt: dim italic
            cursor: '@72'
    Label:
        styles:
            value: dim bold

    Window:
        styles:
            border: '60'
            corner: '60'

    Container:
        styles:
            border: '96'
            corner: '96'
"""


def _define_layout() -> Layout:

    layout = Layout()
    layout.add_slot("Body")

    return layout


class TUI:
    def __init__(self, db_path: str | None) -> None:
        self._db = db_path
        self._sync = SyncManager()
        self.manager = WindowManager()
        self._is_local = bool(db_path)
        self._conn = None

    @property
    def db(self) -> str:
        if self._db is None:
            self._db = self._sync.prepare_local_db()
        return self._db

    @property
    def conn(self) -> Connection:
        if self._conn is None:
            self._conn = lite.connect(self.db)
        return self._conn

    def run_tui(self) -> None:

        self.manager.layout = _define_layout()

        with YamlLoader() as loader:
            loader.load(PYTERMGUI_CONFIG)

        with self.manager:
            """Create the generic main aplication window."""

            main_window = (
                Window(
                    Label(
                        "A CLI tool to manage the database of Bluecoins,\nan awesome budget planner for Android.",
                    ),
                    "",
                    Container(
                        "In development:",
                        Label("- archive"),
                        box="EMPTY_VERTICAL",
                    ),
                    "",
                    Button('Convert', lambda *_: self.manager.add(self.create_currency_window())),
                    "",
                    Button('Archive', lambda *_: self.manager.add(self.create_account_archive_window())),
                    "",
                    Button('Unarchive', lambda *_: self.manager.add(self.create_account_unarchive_window())),
                    "",
                    Button('Sync', lambda *_: self.manager.add(self.create_sync_source_window())),
                    "",
                    Button('Exit programm', lambda *_: self.close_session()),
                    "",
                    width=60,
                    box="DOUBLE",
                )
                .set_title("[210 bold]Cluecoins")
                .center()
            )

            self.manager.add(
                main_window,
                assign="body",
            )

    def create_sync_source_window(self) -> Window:

        source_window = Window(
            "Choose type of synchronization",
            "",
            Button('Local file', lambda *_: self.create_sync_local_window()),
            "",
            Button('Device', lambda *_: self.create_sync_device_window()),
            "",
            Button('Back', lambda *_: self.manager.remove(source_window)),
        ).center()

        return source_window

    def create_sync_local_window(self) -> None:
        files_list = Container(overflow=Overflow.SCROLL, height=10)
        files_list.set_widgets([])

        current_dir = Path.cwd()

        directories: list[Path] = [current_dir.parent]
        files: list[Path] = []

        for path in current_dir.glob('*'):
            if path.is_dir():
                directories.append(path)
            elif path.name.endswith('.fydb'):
                files.append(path)

        for dir in directories:
            button = Button('🌚 ' + dir.name, lambda *_: ...)

            files_list += button

        for file in files:
            button = Button('🌝 ' + str(file.name), lambda *_: ...)

            files_list += button

        sync_local_window = Window(
            'Choos database',
            files_list,
            Button('Back', lambda *_: self.manager.remove(sync_local_window)),
        ).center()

        self.manager.add(sync_local_window)
        sync_local_window.focus()

    def create_sync_device_window(self) -> None:
        from adbutils import adb  # type: ignore[import]

        devices_list = Container(overflow=Overflow.SCROLL, height=10)
        devices_list.set_widgets([])

        adb_diveces_list = adb.device_list()

        for device in adb_diveces_list:
            button = Button(str(device), lambda *_: ...)

            devices_list += button

        device_window = Window(
            'Choos device',
            devices_list,
            Button('Back', lambda *_: self.manager.remove(device_window)),
        ).center()

        self.manager.add(device_window)
        device_window.focus()

    def create_currency_window(self) -> Window:
        '''Create the window to choose a currency and start convert.'''

        def _start(base_currency: str) -> None:
            tmp_window = Window().center() + Label('Please wait...')
            self.manager.add(tmp_window)

            self.start_convert(base_currency)
            self.manager.remove(tmp_window)

        value = 'USD'
        currency_window = Window(
            InputField(prompt='Currency: ', value=value),
            "",
            Button('Convert', lambda *_: _start(value)),
            "",
            Button('Back', lambda *_: self.manager.remove(currency_window)),
        ).center()

        return currency_window

    def create_account_archive_window(self) -> Window:
        """Create the window to choose an account by name and start archive."""

        accounts_table = Container(overflow=Overflow.SCROLL, height=15)
        self._update_accounts_table(accounts_table)

        archive_window = Window(
            accounts_table,
            "",
            Button('Back', lambda *_: self.manager.remove(archive_window)),
        ).center()

        return archive_window

    def create_account_unarchive_window(self) -> Window:
        """Create the window to choose an account by name and start unarchive."""

        archive_accounts_table = Container(overflow=Overflow.SCROLL, height=15)
        self._update_accounts_table(archive_accounts_table, clue=True)

        unarchive_window = Window(
            archive_accounts_table,
            "",
            Button('Back', lambda *_: self.manager.remove(unarchive_window)),
            box="HEAVY",
        ).center()

        return unarchive_window

    def _update_accounts_table(self, accounts_table: Container, clue: bool = False) -> None:
        """Refresh the account_table Container:
        1. Clear the Container.
        2. Fill the container with an (updated) list of accounts from the connected DB.

        Flag CLUE:
            False:
                Work with account archiving.
            True:
                Work with account unarchiving."""

        accounts_table.set_widgets([])

        func = self.start_archive_account
        if clue is True:
            func = self.start_unarchive_account

        for account in get_accounts_list(self.conn, clue):
            account_name = account[0]

            acc = Button(
                label=account_name,
                onclick=partial(func, account_name=account_name),
            )

            accounts_table += acc

    def start_convert(self, base_currency: str) -> None:

        actions.convert(base_currency, self.db)

    def start_archive_account(self, button: Button, account_name: str) -> None:

        actions.archive(account_name, self.db)
        self._update_accounts_table(button.parent)

    def start_unarchive_account(self, button: Button, account_name: str) -> None:

        actions.unarchive(account_name, self.db)
        self._update_accounts_table(button.parent, clue=True)

    def close_session(self) -> None:
        """Run app activity:
                default: opening an app on the phone

        Close terminal interface.
        """

        self.conn.close()

        if not self._is_local:
            # FIXME: hardcode
            self._sync.push_changes_to_app('.ui.activities.main.MainActivity')
        sys.exit(0)
