from decimal import Overflow
import sqlite3 as lite
import sys
from tkinter import ROUND
from tkinter import SCROLL
from tkinter import Label
from tkinter.tix import AUTO

from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets import Label
from pytermgui.widgets.boxes import Box
from pytermgui.widgets.button import Button
from pytermgui.widgets.containers import Container
from pytermgui.widgets.input_field import InputField
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window
from tabulate import tabulate

from bluecoins_cli.adb import execute_cli_command_with_adb
from bluecoins_cli.database import get_account_list

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


def start_convert(base_currency: str) -> None:
    if base_currency == 'USD':
        execute_cli_command_with_adb('convert', '.ui.activities.main.MainActivity')
    else:
        execute_cli_command_with_adb('convert', '.ui.activities.main.MainActivity', base_currency)


def start_archive(account_name: str) -> None:

    execute_cli_command_with_adb('archive', '.ui.activities.main.MainActivity', account_name)


def choose_currency():
    base_currency = 'USD'
    convert_window = Window()

    currency_window = (
        convert_window
        + ""
        + Button(base_currency, lambda *_: start_convert(base_currency))
        + ""
        + Button('Back', lambda *_: manager.remove(convert_window))
    ).center()

    return currency_window


def choose_archive():
    def create_account_table():
        path_test = '/home/larnaa/VScode_project/bluecoins-cli/Bluecoins_last_3.fydb'
        con = lite.connect(path_test)

        account_table = Container()

        for account in get_account_list(con):
            acc = Button(account[0], lambda *_: start_archive(account[0]))
            account_table += acc

        return account_table

    account_table = create_account_table()

    window = Window(box="HEAVY")

    archive_window = (window + "" + account_table + "" + Button('Back', lambda *_: manager.remove(window))).center()

    return archive_window


with YamlLoader() as loader:
    loader.load(PYTERMGUI_CONFIG)

with WindowManager() as manager:
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
            + Button('Convert', lambda *_: manager.add(choose_currency()))
            + ""
            + Button('Archive', lambda *_: manager.add(choose_archive()))
            + ""
            + Button('Exit programm', lambda *_: sys.exit(0))
            + ""
        )
        .set_title("[210 bold]Bluecoins CLI")
        .center()
    )

    manager.add(window)
