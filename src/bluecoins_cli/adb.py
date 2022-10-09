import subprocess

from adbutils import adb  # type: ignore

APP_ID = 'com.rammigsoftware.bluecoins'
DB = "bluecoins-datetime"
cli_command = 'convert'
activity = '.ui.activities.main.MainActivity'

device_list = adb.device_list()

# Date = datetime()


if not device_list:
    raise Exception('Device is not found')
elif len(device_list) >= 2:
    raise Exception('Found two or more devices. Connect only one device.')

device = adb.device(serial=device_list[0].serial)

print(device)
print(device.serial)


# stop bluecoins
device.app_stop(APP_ID)
device.shell(f'pm disable-user --user 0 {APP_ID}')

# adb root (restart adbd as root)
#


def get_app_user_id() -> int:
    user_response = device.shell(f'dumpsys package {APP_ID} | grep userId')
    # split to list, take second element, str --> int
    return int(user_response.split(sep='=')[1])


def pull() -> None:
    subprocess.run(
        f'adb shell su {APP_ID} -c "cat /data/user/0/{APP_ID}/databases/bluecoins.fydb" > {DB}.fydb',
        shell=True,
        check=True,
    )


# pull()


def cli_command_run() -> None:
    subprocess.run(f'poetry run bluecoins-cli {DB}.fydb {cli_command}', shell=True, check=True)


# cli_command_run()


def push_db_root() -> None:

    device.sync.push(f'{DB}.new.fydb', f'/data/local/tmp/{DB}.new.fydb')
    device.shell(f'su 0 -c mv /data/local/tmp/{DB}.new.fydb /data/user/0/{APP_ID}/databases/bluecoins.fydb')

    device.sync.push(f'{DB}.fydb', f'/data/local/tmp/{DB}.fydb')
    device.shell(f'su 0 -c mv /data/local/tmp/{DB}.fydb /data/user/0/{APP_ID}/databases/{DB}.fydb')


device.shell(f'pm enable {APP_ID}')

device.app_start(APP_ID, activity)
