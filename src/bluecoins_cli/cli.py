import logging
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import click

from bluecoins_cli.cache import QuoteCache
from bluecoins_cli.database import delete_account
from bluecoins_cli.database import get_base_currency
from bluecoins_cli.database import iter_accounts
from bluecoins_cli.database import iter_transactions
from bluecoins_cli.database import move_transactions_to_account
from bluecoins_cli.database import open_copy
from bluecoins_cli.database import set_base_currency
from bluecoins_cli.database import transaction
from bluecoins_cli.database import update_account
from bluecoins_cli.database import update_transaction
from bluecoins_cli.storage import BluecoinsStorage
from bluecoins_cli.storage import Storage
from bluecoins_cli.tui import run_tui

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
    _convert(base_currency, ctx.obj['path'])


def _convert(base_currency: str, db_path: str) -> None:

    conn = open_copy(db_path)

    storage = Storage()
    storage.init()
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

        # add labels: cli_archive, cli_%name_acc_old%
        account_id = bluecoins_storage.get_account_id(account_name)

        bluecoins_storage.add_label(account_id, 'cli_archive')
        bluecoins_storage.add_label(account_id, f'cli_{account_name}')

        # move transactions to account Archive
        account_archive_id = bluecoins_storage.get_account_id('Archive')
        move_transactions_to_account(conn, account_id, account_archive_id)

        delete_account(conn, account_id)


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

        account_id = bluecoins_storage.get_account_id(account_name)
        bluecoins_storage.add_label(account_id, label_name)
