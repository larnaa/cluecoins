import logging
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import click
import xdg

from cluecoins.cache import QuoteCache
from cluecoins.database import delete_account
from cluecoins.database import get_base_currency
from cluecoins.database import iter_accounts
from cluecoins.database import iter_transactions
from cluecoins.database import move_transactions_to_account
from cluecoins.database import open_copy
from cluecoins.database import set_base_currency
from cluecoins.database import transaction
from cluecoins.database import update_account
from cluecoins.database import update_transaction
from cluecoins.database import get_accounts_list
from cluecoins.database import find_id_transactions_by_label
from cluecoins.storage import BluecoinsStorage
from cluecoins.storage import Storage
from cluecoins.tui import run_tui
from sqlite3 import Connection

logging.basicConfig(level=logging.DEBUG)


def q(v: Decimal, prec: int = 2) -> Decimal:
    return v.quantize(Decimal(f'0.{prec * "0"}'))


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


@root.command(help='Start user interface')
@click.pass_context
def tui(
    ctx: click.Context,
) -> None:
    run_tui()


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

    conn = open_copy(db_path)

    storage = Storage(Path(xdg.xdg_data_home()) / 'cluecoins' / 'cluecoins.db')
    storage.create_quote_table()
    cache = QuoteCache(storage)

    with transaction(conn) as conn:
        set_base_currency(conn, base_currency)

        for date, id_, rate, currency, amount in iter_transactions(conn):
            true_rate = cache.get_price(date, base_currency, currency)

            amount_original = amount * rate
            amount_quote = amount_original / true_rate

            click.echo(
                f"==> transaction {id_}: {q(amount_original)} {currency} -> {q(amount_quote)} {base_currency} ({q(true_rate)} {base_currency}{currency})"
            )

            update_transaction(conn, id_, true_rate, amount_quote)

        today = datetime.now() - timedelta(days=1)
        for id_, currency, rate in iter_accounts(conn):
            true_rate = cache.get_price(today, base_currency, currency)
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

    conn = open_copy(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        bluecoins_storage.create_account('Archive', account_currency)

        # add labels: clue_%name_acc_old%
        if bluecoins_storage.get_account_id(account_name) is False:
            return print("account is not exist")
        account_id = bluecoins_storage.get_account_id(account_name)

        # Maybe rename to #cli_arcive_{account_name}
        bluecoins_storage.add_label(account_id, f'clue_{account_name}')

        # move transactions to account Archive
        account_archive_id = bluecoins_storage.get_account_id('Archive')
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
    
    conn = open_copy(db_path)

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        # get a list of id transactions on the account
        label_name = 'clue_' + account_name
        id_transactions = find_id_transactions_by_label(conn, label_name)

        # create new account
        account_currency = get_base_currency(conn)
        if bluecoins_storage.create_account(account_name, account_currency) is False:
            return print("account is exist")

        if bluecoins_storage.get_account_id(account_name) is False:
            return print("account is not exist")
        acc_new_id = bluecoins_storage.get_account_id(account_name)

        archive_id = bluecoins_storage.get_account_id('Archive')

        '''
        Move all transaction from Arcive to the new account.
        Delete all labels format: #cli_arcive, #cli_AccountName
        '''


@cli.command(help='Create account with account name')
@click.option('-a', '--account-name', type=str, default='Archive')
@click.pass_context
def create_account(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        bluecoins_storage.create_account(account_name, account_currency)


@cli.command(help='Add label to all account transactions')
@click.option('-a', '--account-name', type=str)
@click.option('-l', '--label-name', type=str)
@click.pass_context
def add_label(
    ctx: click.Context,
    account_name: str,
    label_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        if bluecoins_storage.get_account_id(account_name) is False:
            return print("account is not exist")
        account_id = bluecoins_storage.get_account_id(account_name)
        bluecoins_storage.add_label(account_id, label_name)
