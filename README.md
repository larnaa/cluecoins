> **Non-Affiliation Disclaimer**
>
> This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with [Bluecoins](https://www.bluecoinsapp.com/) app developers. All product and company names are the registered trademarks of their original owners.


# cluecoins 🔍

<img src="https://user-images.githubusercontent.com/49699225/230795265-7bb7849a-1ffe-4468-a63c-af898c5480de.png" align="right" width="480">

Cluecoins is a tool to manage the database of [Bluecoins](https://www.bluecoinsapp.com/). 

**Commands:**
- `convert` - update transactions currency with data from [Exchangerate](https://api.exchangerate.host/timeseries);  
  
- `archive` - archive account, including all transactions  
  (not stable, will soon be rewritten [#55](https://github.com/larnaa/cluecoins/issues/55) - move account and transactions to Cluecoins tables);  
    
- `unarchive` - unarchive account. 
   
**In development:**
- `add-label` - add the label to all transactions of the one account;  

- `create-account` - create a new account.


## Specifics of usage

> **Pre-Release Software**
> 
> That is a pre-release project so it may contain bugs, errors, and other problems. Use at your own risk, and always have a database backup!

Available two types of interfaces:
   - **CLI** - the terminal interface;
   - **TUI** - the graphic interface
      TUI works only with **Android** and **rooted** devices.
        Cluecoins need **root** for access to the directory with `bluecoins.fydb` file - the current database used by Bluecoins.

## Installation

1. `git clone https://github.com/larnaa/cluecoins.git`
2. Go to the directory `cd cluecoins`
3. Install `pip install -e .`

## Startup

1. Connect the device and give the PC access to it.
2. Run Cluecoins TUI `cluecoins tui` or CLI `cluecoins cli`.

### Development mode

> To manage the development environment, you need to have Hatch installed. 

Run `hatch shell` to run an entire development environment. Run `hatch run dev:all` to run an entire CI pipeline: start linters and tests.

## Manual database backup/restore (CLI)

1. Open the Bluecoins app. Go to *Settings -> Data Management -> Phone Storage -> Backup to phone storage*.
2. Transfer created `*.fydb` database backup file to the PC.
3. After performing operations on that file transfer it to the smartphone. Go to *Settings -> Data Management -> Phone Storage -> Restore from phone storage*. Choose created file.

## Backups (TUI)

Cluecoins automatically creates a backup file `backup_{namedb}.fydb` when starting.
