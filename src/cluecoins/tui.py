import sqlite3 as lite
import sys
from functools import partial
from pathlib import Path
from sqlite3 import Connection

from pytermgui.enums import HorizontalAlignment
from pytermgui.enums import Overflow
from pytermgui.file_loaders import YamlLoader
from pytermgui.input import keys
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
    layout.add_slot("Body right", width=0.2)

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

        self.manager.bind(
            keys.RIGHT,
            lambda *_: {
                self.manager.focus(source_window),  # type: ignore
            },
        )

        self.manager.bind(
            keys.LEFT,
            lambda *_: {
                self.manager.focus(main_window),  # type: ignore
            },
        )

        with YamlLoader() as loader:
            loader.load(PYTERMGUI_CONFIG)

        with self.manager:
            """Create the generic main aplication window."""
            source_window = Window(
                "Choose type of synchronization",
                "",
                Button('Local file', lambda *_: self.create_sync_local_window()),
                "",
                Button('Device', lambda *_: self.create_sync_device_window()),
                "",
                box="DOUBLE",
            )

            self.manager.add(
                source_window,
                assign="body_right",
            )

            main_window = Window(
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
                Button('Exit programm', lambda *_: self.close_session()),
                "",
                box="DOUBLE",
            ).set_title("[210 bold]Cluecoins")

            self.manager.add(
                main_window,
                assign="body",
            )

    def create_sync_local_window(self) -> None:
        files_list = Container(overflow=Overflow.SCROLL, height=10)
        current_dir = Path.cwd()

        current_path = Container(
            heigh=2,
        )
        current_path.set_widgets(['Current directory:\n' + str(current_dir)])
        self._update_files_list(files_list, current_dir)

        sync_local_window = Window(
            'Choos database',
            files_list,
            current_path,
            Button('Back', lambda *_: sync_local_window.close()),
        ).center()

        self.manager.add(sync_local_window)
        sync_local_window.focus()

    def _update_files_list(self, files_list: Container, current_dir: Path) -> None:
        """1. Create button 'back to parent directory.'
        2. Clear the Container + add the 'back to parent directory' button.
        3. Sort by directory and *.fydb files, and create buttons.
        4. Fill files_list."""

        files_list.set_widgets([])
        if current_dir != Path('/'):
            back_directory = Button(
                label='/..',
                onclick=partial(self.change_dir, path=current_dir.parents[0]),
                parent_align=HorizontalAlignment.LEFT,
            )
            files_list.set_widgets([back_directory])

        files = current_dir.iterdir()
        for dir in files:
            if dir.is_dir():
                button = Button(
                    label='/' + dir.name,
                    onclick=partial(self.change_dir, path=dir),
                    parent_align=HorizontalAlignment.LEFT,
                )
                files_list += button

        files_fydb = current_dir.glob('*.fydb')
        for file in files_fydb:
            button = Button(
                label='/' + file.name,
                onclick=partial(self.connect_to_local_db),
                parent_align=HorizontalAlignment.LEFT,
            )
            files_list += button

    def change_dir(self, button: Button, path: Path) -> None:
        # current_path.set_widgets(['Current directory:\n' + str(path)])
        self._update_files_list(button.parent, path)

    def connect_to_local_db(self, button: Button) -> None:
        ...

    def create_sync_device_window(self) -> None:
        from adbutils import adb  # type: ignore[import]

        devices_list = Container(overflow=Overflow.SCROLL, height=10)
        devices_list.set_widgets([])

        adb_diveces_list = adb.device_list()

        for device in adb_diveces_list:
            button = Button(
                str(device),
                lambda *_: ...,
                parent_align=HorizontalAlignment.LEFT,
            )

            devices_list += button

        device_window = Window(
            'Choos device',
            devices_list,
            Button('Back', lambda *_: device_window.close()),
        ).center()

        self.manager.add(device_window)
        device_window.focus()

    def create_currency_window(self) -> Window:
        '''Create the window to choose a currency and start convert.'''

        def _start(base_currency: str) -> None:
            tmp_window = Window().center() + Label('Please wait...')
            self.manager.add(tmp_window)

            self.start_convert(base_currency)
            tmp_window.close()

        value = 'USD'
        currency_window = Window(
            InputField(prompt='Currency: ', value=value),
            "",
            Button('Convert', lambda *_: _start(value)),
            "",
            Button('Back', lambda *_: currency_window.close()),
        ).center()

        return currency_window

    def create_account_archive_window(self) -> Window:
        """Create the window to choose an account by name and start archive."""

        accounts_table = Container(overflow=Overflow.SCROLL, height=15)
        self._update_accounts_table(accounts_table)

        archive_window = Window(
            accounts_table,
            "",
            Button('Back', lambda *_: archive_window.close()),
        ).center()

        return archive_window

    def create_account_unarchive_window(self) -> Window:
        """Create the window to choose an account by name and start unarchive."""

        archive_accounts_table = Container(overflow=Overflow.SCROLL, height=15)
        self._update_accounts_table(archive_accounts_table, clue=True)

        unarchive_window = Window(
            archive_accounts_table,
            "",
            Button('Back', lambda *_: unarchive_window.close()),
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
                parent_align=HorizontalAlignment.LEFT,
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
