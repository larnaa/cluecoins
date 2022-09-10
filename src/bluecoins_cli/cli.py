import os
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from email.policy import default
from sqlite3 import Connection

import asyncclick as click
import xdg

from bluecoins_cli.cache import QuoteCache
from bluecoins_cli.database import add_label_to_transaction
from bluecoins_cli.database import create_new_account
from bluecoins_cli.database import delete_account
from bluecoins_cli.database import find_account
from bluecoins_cli.database import find_account_transactions_id
from bluecoins_cli.database import get_base_currency
from bluecoins_cli.database import iter_accounts
from bluecoins_cli.database import iter_transactions
from bluecoins_cli.database import move_transactions_to_account
from bluecoins_cli.database import open_copy
from bluecoins_cli.database import set_base_currency
from bluecoins_cli.database import transaction
from bluecoins_cli.database import update_account
from bluecoins_cli.database import update_transaction


def q(v: Decimal, prec: int = 2) -> Decimal:
    return v.quantize(Decimal(f'0.{prec * "0"}'))


def create_account_def(conn: Connection, account_name: str, account_currency: str) -> None:
    if find_account(conn, account_name) is None:
        create_new_account(conn, account_name, account_currency)


def get_account_id(conn: Connection, account_name: str) -> int:
    account_info = find_account(conn, account_name)
    return account_info[0]


def add_label_to_all_account_transactions(conn: Connection, account_id: int, label_name: str) -> None:
    # find all transation with ID account and add labels with id transactions to LABELSTABEL
    for transaction_id_tuple in find_account_transactions_id(conn, account_id):
        transaction_id = transaction_id_tuple[0]
        add_label_to_transaction(conn, label_name, transaction_id)


@click.group()
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def cli(ctx: click.Context, path: str) -> None:
    ctx.obj = {}
    ctx.obj['path'] = path


@cli.command(help='Convert database to another main currency')
@click.argument('base_currency', default='USD')
@click.pass_context
async def convert(
    ctx: click.Context,
    base_currency: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    cache = QuoteCache(os.path.join(xdg.xdg_cache_home(), 'bluecoins-cli', 'quotes.json'))
    cache.load()

    with transaction(conn) as conn:
        set_base_currency(conn, base_currency)

        for date, id_, rate, currency, amount in iter_transactions(conn):
            true_rate = await cache.get_price(date, base_currency, currency)

            amount_original = amount * rate
            amount_quote = amount_original / true_rate

            click.echo(
                f"==> transaction {id_}: {q(amount_original)} {currency} -> {q(amount_quote)} {base_currency} ({q(true_rate)} {base_currency}{currency})"
            )

            update_transaction(conn, id_, true_rate, amount_quote)

        today = datetime.now() - timedelta(days=1)
        for id_, currency, rate in iter_accounts(conn):
            true_rate = await cache.get_price(today, base_currency, currency)
            update_account(conn, id_, true_rate)
            click.echo(f"==> account {id_}: {q(rate)} {currency} -> {q(true_rate)} {base_currency}{currency}")

    cache.save()


@cli.command(help='Archive account')
@click.option('-a', '--account_name', type=str)
@click.pass_context
async def archive(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    with transaction(conn) as conn:

        # create_archive
        account_currency = get_base_currency(conn)
        create_account_def(conn, 'Archive', account_currency)

        # add_label (2): cli_archive, cli_%name_acc_old%
        account_id = get_account_id(conn, account_name)

        add_label_to_all_account_transactions(conn, account_id, 'cli_archive')
        add_label_to_all_account_transactions(conn, account_id, f'cli_{account_name}')

        # change_account (transaction) to Archive
        account_archive_id = get_account_id(conn, 'Archive')
        move_transactions_to_account(conn, account_id, account_archive_id)

        # delete account
        delete_account(conn, account_archive_id)


@cli.command(help='Create account with account name')
@click.option('-a', '--account_name', type=str, default='Archive')
@click.pass_context
async def create_account(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    with transaction(conn) as conn:

        if find_account(conn, account_name) is None:
            create_new_account(conn, account_name)


@cli.command(help='Add label to all account transactions')
@click.option('-a', '--account_name', type=str)
@click.option('-l', '--label_name', type=str)
@click.pass_context
async def add_label(  # maybe name: add_label_to_all_account_transactions
    ctx: click.Context,
    account_name: str,
    label_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    with transaction(conn) as conn:

        account_info = find_account(conn, account_name)
        account_id = account_info[0]

        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in find_account_transactions_id(conn, account_id):
            transaction_id = transaction_id_tuple[0]
            add_label_to_transaction(conn, label_name, transaction_id)
