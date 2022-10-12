import datetime
from sqlite3 import connect
import subprocess

from adbutils import adb  # type: ignore
from adbutils._device import AdbDevice

class Device:
    def __init__(self, device: AdbDevice) -> None:
        self.device = device

        self.APP_ID = 'com.rammigsoftware.bluecoins'

        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        self.DB = f"bluecoins-{current_time}"


    @classmethod
    def connect(cls) -> 'Device':
        device_list = adb.device_list()

        if not device_list:
            raise Exception('Device is not found')
        elif len(device_list) >= 2:
            raise Exception('Found two or more devices. Connect only one device.')

        device = adb.device(serial=device_list[0].serial)
        return Device(device)


    def stop_app(self) -> None:
        self.device.app_stop(self.APP_ID)
        self.device.shell(f'pm disable-user --user 0 {self.APP_ID}')

    def get_app_user_id(self) -> int:
        user_response = self.device.shell(f'dumpsys package {self.APP_ID} | grep userId')
        # split to list, take second element, str --> int
        return int(user_response.split(sep='=')[1])

    def pull_db(self) -> None:
        subprocess.run(
            f'adb shell su {self.APP_ID} -c "cat /data/user/0/{self.APP_ID}/databases/bluecoins.fydb" > {self.DB}.fydb',
            shell=True,
            check=True,
        )

    def cli_command_run(self, cli_command: str) -> None:
        subprocess.run(f'poetry run bluecoins-cli {self.DB}.fydb {cli_command}', shell=True, check=True)

    def push_db_root(self) -> None:

        self.device.sync.push(f'{self.DB}.new.fydb', f'/data/local/tmp/{self.DB}.new.fydb')
        self.device.shell(
            f'su 0 -c mv /data/local/tmp/{self.DB}.new.fydb /data/user/0/{self.APP_ID}/databases/bluecoins.fydb'
        )

        self.device.sync.push(f'{self.DB}.fydb', f'/data/local/tmp/{self.DB}.fydb')
        self.device.shell(
            f'su 0 -c mv /data/local/tmp/{self.DB}.fydb /data/user/0/{self.APP_ID}/databases/{self.DB}.fydb'
        )

    def start_app(self, activity: str) -> None:
        self.device.shell(f'pm enable {self.APP_ID}')
        self.device.app_start(self.APP_ID, activity)


device = Device.connect()
device.stop_app()
device.pull_db()
device.cli_command_run('convert')
device.push_db_root()
device.start_app('.ui.activities.main.MainActivity')
