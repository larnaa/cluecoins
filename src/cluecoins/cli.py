import logging
import subprocess
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

import click
import xdg

from cluecoins.cache import QuoteCache
from cluecoins.database import connect_local_db
from cluecoins.database import get_base_currency
from cluecoins.database import get_transactions_list
from cluecoins.database import iter_accounts
from cluecoins.database import iter_transactions
from cluecoins.database import set_base_currency
from cluecoins.database import transaction
from cluecoins.database import update_account
from cluecoins.database import update_transaction
from cluecoins.storage import BluecoinsStorage
from cluecoins.storage import Storage

logging.basicConfig(level=logging.DEBUG)


def q(v: Decimal, prec: int = 2) -> Decimal:
    return v.quantize(Decimal(f'0.{prec * "0"}'))


def backup_db(db: Optional[str]) -> None:

    # TODO: add a check if backup_{db} exists
    subprocess.run(
        f'cp {db} backup_{db}',
        shell=True,
        check=True,
    )


@click.group()
@click.pass_context
def root(
    ctx: click.Context,
) -> None:
    ...


@root.group(help='CLI for managing Bluecoins with manual DB addition')
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def cli(ctx: click.Context, path: str) -> None:
    """Manual path database selection."""

    ctx.obj = {}
    ctx.obj['path'] = path
    backup_db(path)


# new option --db
@root.command(help='Start user interface')
@click.option('--db', type=click.Path(exists=True))
@click.pass_context
def tui(ctx: click.Context, db: str | None) -> None:
    from cluecoins.tui import run_tui

    backup_db(db)
    run_tui(db)


@cli.command(help='Convert database to another main currency')
@click.argument('base_currency', default='USD')
@click.pass_context
def convert(
    ctx: click.Context,
    base_currency: str,
) -> None:
    """Convert with CLI (manual DB selection)."""

    _convert(base_currency, ctx.obj['path'])


def _convert(base_currency: str, db_path: str) -> None:

    conn = connect_local_db(db_path)

    storage = Storage(Path(xdg.xdg_data_home()) / 'cluecoins' / 'cluecoins.db')
    storage.create_quote_table()
    cache = QuoteCache(storage)

    with transaction(conn) as conn:
        set_base_currency(conn, base_currency)

        for date, id_, rate, currency, amount in iter_transactions(conn):
            true_rate = cache.get_price(date, base_currency, currency)

            if true_rate == rate:
                continue

            amount_original = amount * rate
            amount_quote = amount_original / true_rate

            update_transaction(conn, id_, true_rate, amount_quote)
            click.echo(
                f"==> transaction {id_}: {q(amount_original)} {currency} -> {q(amount_quote)} {base_currency} ({q(true_rate)} {base_currency}{currency})"
            )

        today = datetime.now() - timedelta(days=1)
        for id_, currency, rate in iter_accounts(conn):
            true_rate = cache.get_price(today, base_currency, currency)

            if true_rate == rate:
                continue

            update_account(conn, id_, true_rate)
            click.echo(f"==> account {id_}: {q(rate)} {currency} -> {q(true_rate)} {base_currency}{currency}")

    storage.commit()


@cli.command(help='Archive account')
@click.option('-a', '--account-name', type=str)
@click.pass_context
def archive(
    ctx: click.Context,
    account_name: str,
) -> None:
    """Archive with CLI (manual DB selection)."""

    _archive(account_name, ctx.obj['path'])


def _archive(
    account_name: str,
    db_path: str,
) -> None:
    """Archive account:
    1. Create CLUE tables, if doesn't exist: 'CLUE_ACCOUNTSTABLE', 'CLUE_TRANSACTIONSTABLE', 'CLUE_LABELSTABLE'
    2. Move the account, transactions, and labels to CLUE tables.
    """

    conn = connect_local_db(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_id = bluecoins_storage.get_account_id(account_name)
        if account_id is None:
            raise Exception(f'Account {account_name} does not exist')

        necessary_tables = ['ACCOUNTSTABLE', 'TRANSACTIONSTABLE', 'LABELSTABLE']
        bluecoins_storage.create_clue_tables(necessary_tables)

        transactions_list = get_transactions_list(conn, account_id)
        for transaction_id in transactions_list:
            bluecoins_storage.move_data_to_table_by_id('LABELSTABLE', 'transactionIDLabels', transaction_id[0])

        bluecoins_storage.move_data_to_table_by_id('TRANSACTIONSTABLE', 'accountID', account_id)

        # NOTE: what to do if account already exist in CLUE_ACCOUNTSTABLE?
        # If account exist - add _2 in the end name of account
        bluecoins_storage.move_data_to_table_by_id('ACCOUNTSTABLE', 'accountsTableID', account_id)


@cli.command(help='Unarchive account')
@click.option('-a', '--account-name', type=str)
@click.pass_context
def unarchive(
    ctx: click.Context,
    account_name: str,
) -> None:
    """Unarchive with CLI (manual DB selection)."""

    _unarchive(account_name, ctx.obj['path'])


def _unarchive(
    account_name: str,
    db_path: str,
) -> None:
    """Move all data: account, transactions, labels; from Cluecoins tables to Bluecoins tables"""

    conn = connect_local_db(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_id = bluecoins_storage.get_account_id(account_name, True)
        if account_id is None:
            raise Exception(f'Account {account_name} does not exist')

        transactions_list = get_transactions_list(conn, account_id, True)
        for transaction_id in transactions_list:
            bluecoins_storage.move_data_to_table_by_id('LABELSTABLE', 'transactionIDLabels', transaction_id[0], True)

        bluecoins_storage.move_data_to_table_by_id('TRANSACTIONSTABLE', 'accountID', account_id, True)

        # NOTE: what to do if account already exist in CLUE_ACCOUNTSTABLE?
        # If account exist - add _2 in the end name of account
        bluecoins_storage.move_data_to_table_by_id('ACCOUNTSTABLE', 'accountsTableID', account_id, True)


# @cli.command(help='Create account with account name')
@click.option('-a', '--account-name', type=str, default='Archive')
@click.pass_context
def create_account(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = connect_local_db(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        bluecoins_storage.create_account(account_name, account_currency)


# @cli.command(help='Add label to all account transactions')
@click.option('-a', '--account-name', type=str)
@click.option('-l', '--label-name', type=str)
@click.pass_context
def add_label(
    ctx: click.Context,
    account_name: str,
    label_name: str,
) -> None:
    conn = connect_local_db(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_id = bluecoins_storage.get_account_id(account_name)
        if account_id is None:
            return print("account is not exist")
        bluecoins_storage.add_label(account_id, label_name)
