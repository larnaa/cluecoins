from subprocess import call

from pytermgui.file_loaders import YamlLoader
from pytermgui.widgets.containers import Container
from pytermgui.widgets.input_field import InputField
from pytermgui.window_manager.manager import WindowManager
from pytermgui.window_manager.window import Window

ADB_SYNC_SCRIPT_PATH = '/home/larnaa/VScode_project/bluecoins-cli/src/bluecoins_cli/adb.py'


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

with YamlLoader() as loader:
    loader.load(PYTERMGUI_CONFIG)

with WindowManager() as manager:
    window = (
        Window(
            "",
            InputField(
                "A CLI tool to manage the database of Bluecoins,\nan awesome budget planner for Android.",
                multiline=True,
            ),
            "",
            Container(
                "In development:",
                InputField("- archive"),
                box="EMPTY_VERTICAL",
            ),
            "",
            [
                "Convert",
                lambda *_: call(
                    ["python", ADB_SYNC_SCRIPT_PATH],
                ),
            ],
            width=60,
            box="DOUBLE",
        )
        .set_title("[210 bold]Bluecoins CLI")
        .center()
    )

    manager.add(window)
