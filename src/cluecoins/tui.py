from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Label
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

from cluecoins.pages import Pages
from cluecoins.tui_actions import Actions

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

    with YamlLoader() as loader:
        loader.load(PYTERMGUI_CONFIG)

    with WindowManager() as manager:
        """Create the generic main aplication window."""

        pages = Pages(db_path)
        actions = Actions(db_path)

        main_window = Window(
            width=60,
            box="DOUBLE",
        ).center()

        window = (
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
            + Button('Convert', lambda *_: manager.add(pages.create_currency_window(manager)))
            + ""
            + Button('Archive', lambda *_: manager.add(pages.create_account_archive_window(manager)))
            + ""
            + Button('Unarchive', lambda *_: manager.add(pages.create_account_unarchive_window(manager)))
            + ""
            + Button('Exit programm', lambda *_: actions.close_session())
            + ""
        ).set_title("[210 bold]Cluecoins")

        manager.add(window)
