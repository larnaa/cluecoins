import datetime
import subprocess

from adbutils import adb  # type: ignore
from adbutils._device import AdbDevice  # type: ignore


class Device:
    def __init__(self, device: AdbDevice) -> None:
        self.DEVICE = device
        self.APP_ID = 'com.rammigsoftware.bluecoins'

    @classmethod
    def connect(cls) -> 'Device':
        device_list = adb.device_list()

        if not device_list:
            raise Exception('Device is not found')
        elif len(device_list) >= 2:
            raise Exception('Found two or more devices. Connect only one device.')

        device = adb.device(serial=device_list[0].serial)
        return Device(device)

    @staticmethod
    def create_db() -> str:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        return f"bluecoins-{current_time}"

    def stop_app(self) -> None:
        self.DEVICE.app_stop(self.APP_ID)
        self.DEVICE.shell(f'pm disable-user --user 0 {self.APP_ID}')

    def get_app_user_id(self) -> int:
        user_response = self.DEVICE.shell(f'dumpsys package {self.APP_ID} | grep userId')
        # NOTE: split to list, take second element, str --> int
        return int(user_response.split(sep='=')[1])

    def pull_db(self, db: str) -> None:
        subprocess.run(
            f'adb shell su {self.APP_ID} -c "cat /data/user/0/{self.APP_ID}/databases/bluecoins.fydb" > {db}.fydb',
            shell=True,
            check=True,
        )

    def cli_command_run(self, cli_command: str, db: str) -> None:
        subprocess.run(f'bluecoins-cli {db}.fydb {cli_command}', shell=True, check=True)

    def push_db_root(self, db: str) -> None:

        self.DEVICE.sync.push(f'{db}.new.fydb', f'/data/local/tmp/{db}.new.fydb')
        # FIXME: don't use root
        self.DEVICE.shell(
            f'su 0 -c mv /data/local/tmp/{db}.new.fydb /data/user/0/{self.APP_ID}/databases/bluecoins.fydb'
        )

        self.DEVICE.sync.push(f'{db}.fydb', f'/data/local/tmp/{db}.fydb')
        # FIXME: don't use root
        self.DEVICE.shell(f'su 0 -c mv /data/local/tmp/{db}.fydb /data/user/0/{self.APP_ID}/databases/{db}.fydb')

    def start_app(self, activity: str) -> None:
        self.DEVICE.shell(f'pm enable {self.APP_ID}')
        self.DEVICE.app_start(self.APP_ID, activity)


device = Device.connect()
device.stop_app()
db = device.create_db()
device.pull_db(db)
device.cli_command_run('convert', db)
device.push_db_root(db)
device.start_app('.ui.activities.main.MainActivity')
