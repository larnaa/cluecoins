.ONESHELL:
.PHONY: test build
.DEFAULT_GOAL: all

DEV=1
TAG=latest

all: install lint test cover
lint: isort black flake mypy

install:
	poetry install \
	`if [ "${DEV}" = "0" ]; then echo "--no-dev"; fi`

isort:
	poetry run isort src tests

black:
	poetry run black src tests

flake:
	poetry run flakeheaven lint src tests

mypy:
	poetry run mypy src tests --strict

test:
	poetry run pytest --cov-report=term-missing --cov=bluecoins_cli --cov-report=xml -n auto --dist loadscope -s -v tests

cover:
	poetry run diff-cover --compare-branch=master coverage.xml

build:
	poetry build

release-patch:
	bumpversion patch
	git push --tags
	git push

release-minor:
	bumpversion minor
	git push --tags
	git push

release-major:
	bumpversion major
	git push --tags
	git push

adb-sync:
	set -e
	export DB="bluecoins-$(date +%s)"
	adb shell am force-stop com.rammig.bluecoins
	adb shell su 10128 -c "cat /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb" > ${DB}.fydb
	poetry run bluecoins-cli ${DB}.fydb convert
	adb push ${DB}.new.fydb /data/local/tmp/${DB}.new.fydb
	adb push ${DB}.fydb /data/local/tmp/${DB}.fydb
	adb shell su 0 -c mv /data/local/tmp/${DB}.new.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/bluecoins.fydb
	adb shell su 0 -c mv /data/local/tmp/${DB}.fydb /data/user/0/com.rammigsoftware.bluecoins/databases/${DB}.fydb
	adb shell am start -n com.rammigsoftware.bluecoins/.ui.activities.main.MainActivity
