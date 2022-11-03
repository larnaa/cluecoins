from bluecoins_cli.adb import Device
from bluecoins_cli.adb import generate_new_db_name


class SyncManager:
    """
    Class functions:
        1. create empty db with new name
        2. pull db
        3. push db
        4. clone db
        5. track db state
    """

    def __init__(self) -> None:
        self.db = generate_new_db_name()
        self.device: Device | None = None

    def get_device(self) -> Device:
        if self.device is None:
            self.device = Device.connect()
        return self.device

    def prepare_local_db(self) -> str:
        device = self.get_device()
        device.stop_app()
        device.pull_db(self.db)
        return f'{self.db}.fydb'

    def push_changes_to_app(self, activity: str) -> None:
        device = self.get_device()
        device.push_db_root(self.db)
        device.start_app(activity)
