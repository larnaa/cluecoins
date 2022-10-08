from adbutils import adb  # type: ignore

APP_ID = 'com.rammigsoftware.bluecoins'
DB = "bluecoins-datetime"

device_list = adb.device_list()


if not device_list:
    raise Exception('Device is not found')
elif len(device_list) >= 2:
    raise Exception('Found two or more devices. Connect only one device.')

for info in device_list:
    device_id = info.serial

#   export DB="bluecoins-$(date +%s)"
# 	adb shell am force-stop ${APP_ID}
#   adb shell dumpsys package com.example.myapp | grep userId=
# 	adb shell su 10128 -c "cat /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb" > ${DB}.fydb
# 	poetry run bluecoins-cli ${DB}.fydb convert
# 	adb push ${DB}.new.fydb /data/local/tmp/${DB}.new.fydb
# 	adb push ${DB}.fydb /data/local/tmp/${DB}.fydb
# 	adb shell su 0 -c mv /data/local/tmp/${DB}.new.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb
# 	adb shell su 0 -c mv /data/local/tmp/${DB}.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/${DB}.fydb
# 	adb shell am start -n com.rammigsoftware.bluecoins/.ui.activities.main.MainActivity
