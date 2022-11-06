> **Non-Affiliation Disclaimer**
>
> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with [Bluecoins](https://www.bluecoinsapp.com/) app developers. All product and company names are the registered trademarks of their original owners.

> **Pre-Release Software**
> 
> This project is at the pre-release stage and may contain bugs, errors and other problems. Use at your own risk and make sure to always have a database backup!

# cluecoins 🔍

A tool to manage the database of [Bluecoins](https://www.bluecoinsapp.com/), a finance manager for Android.

## Installation

Cluecoins is not released yet. You need to build it from sources.

To manage development environment you need GNU Make and [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) installed.  
Run `poetry build` to make a Python wheel package. Run `make` to run an entire CI pipeline: install dependencies, run linters and tests.

## Usage

Run `cluecoins` command and follow the instructions.

## Console interface

You need to pull database first with **FIXME** command or manually.

Perform operations on that file with `cluecoins db <filename> <command>`. For example, `cluecoins db test.fydb convert` will convert database to another base currency.

## Manual database backup/restore

1. Open the Bluecoins app. Go to *Settings -> Data Management -> Phone Storage -> Backup to phone storage*.
2. Transfer created `*.fydb` database backup file to the PC.
3. After performing operations on that file transfer it to the smartphone. Go to *Settings -> Data Management -> Phone Storage -> Restore from phone storage*. Choose created file.

