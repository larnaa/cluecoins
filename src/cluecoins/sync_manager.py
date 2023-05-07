import shutil
from pathlib import Path

from cluecoins.adb import Device
from cluecoins.adb import generate_new_db_name


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

    def prepare_remote_db(self) -> str:
        device = self.get_device()
        device.stop_app()
        device.pull_db(self.db)
        return f'{self.db}.fydb'

    def push_changes_to_app(self, activity: str) -> None:
        device = self.get_device()
        device.push_db_root(self.db)
        device.start_app(activity)


class SyncManagerDB:
    def __init__(self) -> None:
        self.db = generate_new_db_name()

    def backup(self, path: Path) -> None:
        if not str(path).endswith('.fydb'):
            raise Exception('wrong extension')

        backup_dir = Path.home() / '.local/share/cluecoins/'

        if not backup_dir.is_dir():
            backup_dir.mkdir(parents=True, exist_ok=True)

        backup_path = backup_dir / f'{self.db}.fydb'
        shutil.copyfile(path, backup_path)
