import sqlite3 as lite
import sys
from functools import partial

from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Label
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.widgets.input_field import InputField
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

import cluecoins.cli as cli
from cluecoins.database import get_accounts_list
from cluecoins.database import get_archived_accounts
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


def run_tui(db_path: str | None) -> None:

    sync = SyncManager()

    def get_db() -> str:
        if not db_path:
            return sync.prepare_local_db()
        return db_path

    def create_currency_window(manager: WindowManager) -> Window:
        '''Create the window to choose a currency and start convert.'''

        window = Window()

        def _start(base_currency: str) -> None:
            tmp_window = Window().center() + Label('Please wait...')
            manager.add(tmp_window)
            start_convert(base_currency)
            manager.remove(tmp_window)

        currency_field = InputField(prompt='Currency: ', value='USD')
        currency_window = (
            window
            + ""
            + currency_field
            + ""
            + Button('Convert', lambda *_: _start(currency_field.value))
            + ""
            + Button('Back', lambda *_: manager.remove(window))
        ).center()

        return currency_window

    def create_account_archive_window(manager: WindowManager) -> Window:
        """Create the window to choose an account by name and start archive.

        Create an accounts info table.
        """

        con = lite.connect(get_db())

        accounts_table = Container()

        for account in get_accounts_list(con):
            account_name = account[0]
            acc = Button(
                account_name,
                partial(start_archive_account, account_name=account_name),
            )
            accounts_table += acc

        window = Window(box="HEAVY")

        archive_window = (
            window + "" + accounts_table + "" + Button('Back', lambda *_: manager.remove(window))
        ).center()

        return archive_window

    def create_account_unarchive_window(manager: WindowManager) -> Window:
        """Create the window to choose an account by name and start unarchive.

        Create an accounts info table.
        """

        con = lite.connect(get_db())

        unarchive_accounts_table = Container()

        for account in get_archived_accounts(con):
            account_name = account[0]
            acc = Button(
                label=account_name,
                onclick=partial(start_unarchive_account, account_name=account_name),
            )
            unarchive_accounts_table += acc

        window = Window(box="HEAVY")

        unarchive_window = (
            window + "" + unarchive_accounts_table + "" + Button('Back', lambda *_: manager.remove(window))
        ).center()

        return unarchive_window

    def start_convert(base_currency: str) -> None:

        cli._convert(base_currency, get_db())

    def start_archive_account(button: Button, account_name: str) -> None:

        cli._archive(account_name, get_db())

    def start_unarchive_account(button: Button | None, account_name: str) -> None:

        cli._unarchive(account_name, get_db())

    def close_session() -> None:
        """Run app activity:
                default: opening an app on the phone

        Close terminal interface.
        """

        if not db_path:
            # FIXME: hardcode
            sync.push_changes_to_app('.ui.activities.main.MainActivity')
        sys.exit(0)

    with YamlLoader() as loader:
        loader.load(PYTERMGUI_CONFIG)

    with WindowManager() as manager:
        """Create the generic main aplication window."""

        main_window = Window(width=60, box="DOUBLE")

        window = (
            (
                main_window
                + ""
                + Label(
                    "A CLI tool to manage the database of Bluecoins,\nan awesome budget planner for Android.",
                )
                + ""
                + Container(
                    "In development:",
                    Label("- archive"),
                    box="EMPTY_VERTICAL",
                )
                + ""
                + Button('Convert', lambda *_: manager.add(create_currency_window(manager)))
                + ""
                + Button('Archive', lambda *_: manager.add(create_account_archive_window(manager)))
                + ""
                + Button('Unarchive', lambda *_: manager.add(create_account_unarchive_window(manager)))
                + ""
                + Button('Exit programm', lambda *_: close_session())
                + ""
            )
            .set_title("[210 bold]Bluecoins CLI")
            .center()
        )

        manager.add(window)
