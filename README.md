> **Non-Affiliation Disclaimer**
>
> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with [Bluecoins](https://www.bluecoinsapp.com/) app developers. All product and company names are the registered trademarks of their original owners.

> **Pre-Release Software**
> 
> This project is at the pre-release stage and may contain bugs, errors and other problems. Use at your own risk and make sure to always have a database backup!

# cluecoins 🔍

A tool to manage the database of [Bluecoins](https://www.bluecoinsapp.com/), a finance manager for Android.

Cluecoins can be used in two ways: by CLI or TUI.

## Installation

Cluecoins is not released yet. You need to build it from sources.

To use the Cluecoins you need [Hatch](https://hatch.pypa.io/1.5/install/) installed.

1. ```git clone https://github.com/larnaa/cluecoins.git```
2. Run `hatch run cluecoins tui` to start work with Cluecoins.

 >Run `hatch shell` to run an entire development environment.

## Manual database backup/restore

1. Open the Bluecoins app. Go to *Settings -> Data Management -> Phone Storage -> Backup to phone storage*.
2. Transfer created `*.fydb` database backup file to the PC.
3. After performing operations on that file transfer it to the smartphone. Go to *Settings -> Data Management -> Phone Storage -> Restore from phone storage*. Choose created file.

