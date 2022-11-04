# Cluecoins

A CLI and TUI tool to manage the database of Bluecoins.

> ❗ **IMPORTANT** ❗
>
> **All rights to the fantastic Bluecoins Android budget planner belong to [Bluecoins](https://www.bluecoinsapp.com/)** 

> 🚧 **WARNING** 🚧
> 
> This sortware is at the very early stage of development. Use at your own risk and make sure to always have a database backup!

## Contents
- [Installation](#installation)
- [CLI Usage](#cli-usage)
- [TUI Usage](#tui-usage)

## Installation

You need GNU Make and [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) installed.  
Run `make` to perform an entire CI pipeline - install dependencies, run linters and tests.

## CLI Usage

1. Open the Bluecoins app. Go to *Settings -> Data Management -> Phone Storage -> Backup to phone storage*.
2. Transfer created `*.fydb` database backup file to the PC.
3. Run `cluecoins mybackup.fydb convert` to convert a database to USD base currency.
4. Transfer created `mybackup.new.fydb` file to the smartphone. Go to *Settings -> Data Management -> Phone Storage -> Restore from phone storage*. Choose created file.

## TUI Usage

Run `cluecoins`.
