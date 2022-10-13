
from turtle import home
import pytermgui as ptg
from subprocess import call

PATH = '/home/larnaa/VScode_project/bluecoins-cli/src/bluecoins_cli/adb.py'


CONFIG = """
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

with ptg.YamlLoader() as loader:
    loader.load(CONFIG)

with ptg.WindowManager() as manager:
    window = (
        ptg.Window(
            "",
            ptg.InputField("A CLI tool to manage the database of Bluecoins,\nan awesome budget planner for Android.", multiline=True),
            "",
            ptg.Container(
                "In developing:",
                ptg.InputField(
                    "- archive"
                ),
                box="EMPTY_VERTICAL",
            ),
            "",
            ["Convert", lambda *_: call(["python", PATH])],
            width=60,
            box="DOUBLE",
        )
        .set_title("[210 bold]Bluecoins CLI")
        .center()
    )

    manager.add(window)


