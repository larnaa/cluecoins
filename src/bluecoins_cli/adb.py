from pathlib import Path

from adbutils import adb  # type: ignore

APP_ID = 'com.rammigsoftware.bluecoins'
DB = "bluecoins-datetime"

device_list = adb.device_list()


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
# device.root()


def get_app_user_id() -> int:
    user_response = device.shell(f'dumpsys package {APP_ID} | grep userId')
    # split to list, take second element, str --> int
    return int(user_response.split(sep='=')[1])


def pull() -> None:
    bluecoins_database = device.shell(
        f'su {get_app_user_id()} -c "cat /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb"'
    )
    local_path = Path(f'{DB}.fydb')
    local_path.write_bytes(bluecoins_database.encode())

pull()


# run bluecoins
device.shell(f'pm enable {APP_ID}')


#   export DB="bluecoins-$(date +%s)"
# 	+ adb shell am force-stop ${APP_ID}
#   + adb shell pm disable-user --user 0 com.rammigsoftware.bluecoins
#   + adb shell dumpsys package com.rammigsoftware.bluecoins | grep userId
# 	+ adb shell su 10128 -c "cat /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb" > ${DB}.fydb
# 	poetry run bluecoins-cli ${DB}.fydb convert
# 	adb push ${DB}.new.fydb /data/local/tmp/${DB}.new.fydb
# 	adb push ${DB}.fydb /data/local/tmp/${DB}.fydb
# 	adb shell su 0 -c mv /data/local/tmp/${DB}.new.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb
# 	adb shell su 0 -c mv /data/local/tmp/${DB}.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/${DB}.fydb
# 	adb shell am start -n com.rammigsoftware.bluecoins/.ui.activities.main.MainActivity
#   + adb shell pm enable com.rammigsoftware.bluecoins
