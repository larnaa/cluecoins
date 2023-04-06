> **Non-Affiliation Disclaimer**
>
> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with [Bluecoins](https://www.bluecoinsapp.com/) app developers. All product and company names are the registered trademarks of their original owners.


# cluecoins 🔍

A tool to manage the database of [Bluecoins](https://www.bluecoinsapp.com/) for Android.

Now available command: 
1. Convert the database to another main currency;
2. Archive accounts (not stable because this command is based on labels);
3. Unarchive accounts.
   
In development:
1. Add the label to all transactions of the one account;
2. Create a new account.

## Specifics of usage

> **Pre-Release Software**
> 
> This project is at the pre-release stage and may contain bugs, errors and other problems. Use at your own risk and make sure to always have a database backup!

1. This project is focused only on **Android** devices.
2. You need a **rooted** device to use Cluecoins.
3. There are two ways to use it: the terminal interface (**CLI**) and the user interface (**TUI**).

## Installation

1. `git clone https://github.com/larnaa/cluecoins.git`
2. Go to the directory `cd cluecoins`
3. Install `pip install -e .`

## Startup

1. Connect device. Don't forget to give access to the device when you start the application.
2. Run Cluecoins TUI `cluecoins tui` or CLI `cluecoins cli`.

### Development mode

> To manage development environment you need Hatch installed.  

Run `hatch shell` to run an entire development environment. Run `hatch run dev:all` to run an entire CI pipeline: start linters, tests and cover.

## Manual database backup/restore (CLI)

1. Open the Bluecoins app. Go to *Settings -> Data Management -> Phone Storage -> Backup to phone storage*.
2. Transfer created `*.fydb` database backup file to the PC.
3. After performing operations on that file transfer it to the smartphone. Go to *Settings -> Data Management -> Phone Storage -> Restore from phone storage*. Choose created file.


## Backups (TUI)

You can find the backup DB in the backups directory of Bluecoins.

```
/data/user/0/com.rammigsoftware.bluecoins/databases/cluecoins-{saved_time}.fydb
```
