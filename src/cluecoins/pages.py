import sqlite3 as lite
from functools import partial

from pytermgui.widgets import Label
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.widgets.input_field import InputField
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

from cluecoins.database import get_accounts_list
from cluecoins.tui_actions import Actions


class Pages:
    def __init__(self, db_path: str | None) -> None:
        self._actions = Actions(db_path)

    def create_currency_window(self, manager: WindowManager) -> Window:
        '''Create the window to choose a currency and start convert.'''

        window = Window()

        def _start(base_currency: str) -> None:
            tmp_window = Window().center() + Label('Please wait...')
            manager.add(tmp_window)

            self._actions.start_convert(base_currency)
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

    def create_account_archive_window(self, manager: WindowManager) -> Window:
        """Create the window to choose an account by name and start archive.

        Create an accounts info table.
        """

        conn = lite.connect(self._actions.db)

        accounts_table = Container()

        for account in get_accounts_list(conn):
            account_name = account[0]
            acc = Button(
                account_name,
                partial(self._actions.start_archive_account, account_name=account_name),
            )
            accounts_table += acc

        window = Window(
            box="HEAVY",
        ).center()

        archive_window = window + "" + accounts_table + "" + Button('Back', lambda *_: manager.remove(window))

        return archive_window

    def create_account_unarchive_window(self, manager: WindowManager) -> Window:
        """Create the window to choose an account by name and start unarchive.

        Create an accounts info table.
        """

        conn = lite.connect(self._actions.db)

        unarchive_accounts_table = Container()

        for account in get_accounts_list(conn, clue=True):
            account_name = account[0]
            acc = Button(
                label=account_name,
                onclick=partial(self._actions.start_unarchive_account, account_name=account_name),
            )
            unarchive_accounts_table += acc

        window = Window(box="HEAVY")

        unarchive_window = (
            window + "" + unarchive_accounts_table + "" + Button('Back', lambda *_: manager.remove(window))
        ).center()

        return unarchive_window
