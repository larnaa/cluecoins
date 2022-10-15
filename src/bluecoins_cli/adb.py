import datetime
import subprocess

from adbutils import adb  # type: ignore
from adbutils._device import AdbDevice  # type: ignore

APP_ID = 'com.rammigsoftware.bluecoins'


def get_db_name() -> str:
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    return f"bluecoins-{current_time}"


class Device:
    def __init__(self, device: AdbDevice) -> None:
        self.device = device

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
        self.device.app_stop(APP_ID)
        self.device.shell(f'pm disable-user --user 0 {APP_ID}')

    def get_app_user_id(self) -> int:
        user_response = self.device.shell(f'dumpsys package {APP_ID} | grep userId')
        # NOTE: split to list, take second element, str --> int
        return int(user_response.split(sep='=')[1])

    def pull_db(self, db: str) -> None:
        subprocess.run(
            f'adb shell su {APP_ID} -c "cat /data/user/0/{APP_ID}/databases/bluecoins.fydb" > {db}.fydb',
            shell=True,
            check=True,
        )

    def cli_command_run(self, cli_command: str, db: str, keys: str) -> None:
        subprocess.run(f'bluecoins-cli {db}.fydb {cli_command}{keys}', shell=True, check=True)

    def push_db_root(self, db: str) -> None:

        self.device.sync.push(f'{db}.new.fydb', f'/data/local/tmp/{db}.new.fydb')
        # FIXME: don't use root
        self.device.shell(f'su 0 -c mv /data/local/tmp/{db}.new.fydb /data/user/0/{APP_ID}/databases/bluecoins.fydb')

        self.device.sync.push(f'{db}.fydb', f'/data/local/tmp/{db}.fydb')
        # FIXME: don't use root
        self.device.shell(f'su 0 -c mv /data/local/tmp/{db}.fydb /data/user/0/{APP_ID}/databases/{db}.fydb')

    def start_app(self, activity: str) -> None:
        self.device.shell(f'pm enable {APP_ID}')
        self.device.app_start(APP_ID, activity)


def execute_cli_command_with_adb(cli_command: str, activity: str, keys_value: str = '') -> None:
    # TODO: create func: keys --> each key has separate variable
    if keys_value != '':
        keys = (f'--{keys_value}')
    else:
        keys = ''

    device = Device.connect()
    device.stop_app()
    db = get_db_name()
    device.pull_db(db)
    device.cli_command_run(cli_command, db, keys)
    device.push_db_root(db)
    device.start_app(activity)
