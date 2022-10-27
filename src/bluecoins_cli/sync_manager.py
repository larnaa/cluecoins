from bluecoins_cli.adb import Device
from bluecoins_cli.adb import generate_new_db_name

device = Device.connect()


class SyncManager:
    """
    1. create empty db with new name
    2. pull db
    3. push db
    4. clone db
    5. track db state
    """

    def __init__(self) -> None:
        self.db = generate_new_db_name()

    def prepare_local_db(self) -> str:
        device.stop_app()
        device.pull_db(self.db)
        return f'{self.db}.fydb'

    def push_changes_to_app(self, activity: str) -> None:
        device.push_db_root(self.db)
        device.start_app(activity)
