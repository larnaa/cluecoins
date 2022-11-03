import sqlite3 as lite
import sys
from functools import partial

from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Label
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

from bluecoins_cli.database import get_account_list
from bluecoins_cli.sync_manager import SyncManager

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


def run_tui() -> None:

    sync = SyncManager()
    db = sync.prepare_local_db()

    def get_choose_currency_window(manager: WindowManager) -> Window:
        """Create the window to choose a currency and start convert."""

        # FIXME: hardcode
        base_currency = 'USD'
        window = Window()

        currency_window = (
            window
            + ""
            + Button(base_currency, lambda *_: start_convert(base_currency))
            + ""
            + Button('Back', lambda *_: manager.remove(window))
        ).center()

        return currency_window

    def get_choose_account_archive_window(manager: WindowManager) -> Window:
        """Create the window to choose an account by name and start archive.

        Create an account info table.
        """

        # FIXME: when you select several accounts, only the last one clicked is archived.

        con = lite.connect(db)

        account_table = Container()

        for account in get_account_list(con):
            account_name = account[0]
            acc = Button(
                account_name,
                partial(start_archive_account, account_name=account_name),
            )
            account_table += acc

        window = Window(box="HEAVY")

        archive_window = (window + "" + account_table + "" + Button('Back', lambda *_: manager.remove(window))).center()

        return archive_window

    def start_convert(base_currency: str) -> None:
        import bluecoins_cli.cli as cli

        cli._convert(base_currency, db)

    def start_archive_account(button: Button, account_name: str) -> None:
        import bluecoins_cli.cli as cli

        cli._archive(account_name, db)

    def close_session() -> None:
        """Run app activity:
                default: opening an app on the phone

        Close terminal interface.
        """

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
                + Button('Convert', lambda *_: manager.add(get_choose_currency_window(manager)))
                + ""
                + Button('Archive', lambda *_: manager.add(get_choose_account_archive_window(manager)))
                + ""
                + Button('Exit programm', lambda *_: close_session())
                + ""
            )
            .set_title("[210 bold]Bluecoins CLI")
            .center()
        )

        manager.add(window)
