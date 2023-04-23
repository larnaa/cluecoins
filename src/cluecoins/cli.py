import logging
import subprocess
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional
import re

import click
import xdg

from cluecoins.cache import QuoteCache
from cluecoins.database import ENCODED_LABEL_PREFIX
from cluecoins.database import LABEL_PREFIX
from cluecoins.database import connect_local_db
from cluecoins.database import create_archived_account
from cluecoins.database import delete_account
from cluecoins.database import delete_label
from cluecoins.database import find_labels_by_transaction_id
from cluecoins.database import find_transactions_by_label
from cluecoins.database import get_base_currency
from cluecoins.database import iter_accounts
from cluecoins.database import iter_transactions
from cluecoins.database import move_transactions_to_account
from cluecoins.database import move_transactions_to_account_with_id
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

    conn = connect_local_db(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        bluecoins_storage.create_account('Archive', account_currency)

        # FIXME: NULL is written as None
        account_info_base64 = bluecoins_storage.encode_account_info(account_name)

        account_id = bluecoins_storage.get_account_id(account_name)
        if account_id is None:
            return None  # account does not exist -> exception

        # Maybe rename to #clue_arcive_{account_name}
        bluecoins_storage.add_label(account_id, f'{LABEL_PREFIX}{account_name}')
        bluecoins_storage.add_label(account_id, f'{ENCODED_LABEL_PREFIX}{account_info_base64}')

        # move transactions to account Archive
        account_archive_id = bluecoins_storage.get_account_id('Archive')
        if account_archive_id is None:
            return None  # account does not exist ->  -> exception
        move_transactions_to_account(conn, account_id, account_archive_id)

        delete_account(conn, account_id)


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

    conn = connect_local_db(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        # create account
        account_info = bluecoins_storage.decode_account_info(account_name)
        create_archived_account(conn, account_info)

        label_name = 'clue_' + account_name
        id_transactions = find_transactions_by_label(conn, label_name)

        # get account IDs
        acc_new_id = bluecoins_storage.get_account_id(account_name)
        if acc_new_id is None:
            return None  # account does not exist -> exception

        # move transactions
        for id in id_transactions:
            move_transactions_to_account_with_id(conn, id[0], acc_new_id)

            delete_label(conn, label_name)

            labels_list = find_labels_by_transaction_id(conn, id[0])
            for label in labels_list:
                if label[0].startswith(ENCODED_LABEL_PREFIX):
                    delete_label(conn, label[0])


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


@cli.command(help='Archive account')
@click.option('-a', '--account-name', type=str)
@click.pass_context
def archive_v2(
    ctx: click.Context,
    account_name: str,
) -> None:
    """Archive with CLI (manual DB selection)."""

    _archive_v2(account_name, ctx.obj['path'])


def _archive_v2(
    account_name: str,
    db_path: str,
) -> None:

    conn = connect_local_db(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        # write schema in variable like str
        path = Path(__file__).parent / 'bluecoins.sql'
        schema = path.read_text()

        # get schema
        query_list = schema.split(';')

        # check existence account
        account_id = bluecoins_storage.get_account_id(account_name)
        if account_id is None:
            return None  # account does not exist -> exception
        
        # create tables if not exist
        necessary_tables = ['ACCOUNTSTABLE', 'TRANSACTIONSTABLE', 'LABELSTABLE']

        for query in query_list:

            regex = 'CREATE TABLE (\w*)'
            
            re_query = re.search(regex, query)
            if re_query is None: # check: CREATE TABLE or CREATE INDEX
                continue

            table_blue = re_query.group(1) # from Bluecoins DB
            if table_blue not in necessary_tables: # check: included table from Bluecoins DB in necessary_tables
                continue
            part_of_blue_query = re_query.group(0)
            
            clue_table = f'CLUE_{table_blue}'
            
            clue_table_query = query.replace(part_of_blue_query, f'CREATE TABLE IF NOT EXISTS {clue_table}')
            # create table
            conn.cursor().execute(clue_table_query)

        # move account
        conn.cursor().execute(
            'INSERT INTO CLUE_ACCOUNTSTABLE SELECT * FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
            (account_id,),
        )
        conn.cursor().execute(
            'DELETE FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
            (account_id,),
        )

        # get transactions list
        transactions = conn.cursor().execute(
            'SELECT transactionsTableID FROM TRANSACTIONSTABLE ',
        )
        transactions_list = transactions.fetchall()

        # move transactions
        # for transaction_id in transactions_list:
        #     transaction_id = transaction_id[0]
        conn.cursor().execute(
            'INSERT INTO CLUE_TRANSACTIONSTABLE SELECT * FROM TRANSACTIONSTABLE WHERE accountID = ?',
            (account_id,),
        )
        conn.cursor().execute(
            'DELETE FROM TRANSACTIONSTABLE WHERE accountID = ?',
            (account_id,),
        )

        # move labels
        for transaction_id in transactions_list:
            conn.cursor().execute(
                'INSERT INTO CLUE_LABELSTABLE SELECT * FROM LABELSTABLE WHERE transactionIDLabels = ?',
                (transaction_id[0],),
            )
            conn.cursor().execute(
                'DELETE FROM LABELSTABLE WHERE transactionIDLabels = ?',
                (transaction_id[0],),
            )

        # create_cluecoins_table(conn, ...)

        # check by name - account exist or not
        # create cluecoins tables
        # move data (account, transactions, lables (?) from bluecoins table to cluecoins table
        ...

_archive_v2('Sberbank', "Bluecoins_db_6copy.fydb")

'''
import sqlite3

cursor = conn.cursor()
list_of_tables_names = cursor.execute("SELECT name FROM sqlite_master;") # tables names
list_of_queries = cursor.execute("SELECT sql FROM sqlite_master;") # queries

'''