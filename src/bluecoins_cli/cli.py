import logging
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import asyncclick as click

from bluecoins_cli.adb import Device
from bluecoins_cli.adb import get_db_name
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
):
    ...


@root.group(help='Start CLI')
@click.argument('path', type=click.Path(exists=True))
@click.pass_context
def cli(ctx: click.Context, path: str) -> None:
    ctx.obj = {}
    ctx.obj['path'] = path


@root.command(help='Start TUI')
@click.pass_context
async def tui(
    ctx: click.Context,
    cli_command: str,
    activity: str,
    keys_value: str = '',
) -> None:
    # create object Device
    device = Device.connect()
    db = get_db_name()

    # run tui
    device.stop_app()
    db = get_db_name()
    device.pull_db(db)
    run_tui()

    # TODO: create func: keys --> each key has separate variable
    if keys_value != '':
        keys = f'--{keys_value}'
    else:
        keys = ''

    device.cli_command_run(cli_command, db, keys)
    device.push_db_root(db)
    device.start_app(activity)


@cli.command(help='Convert database to another main currency')
@click.argument('base_currency', default='USD')
@click.pass_context
async def convert(
    ctx: click.Context,
    base_currency: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    storage = Storage()
    storage.init()
    cache = QuoteCache(storage)

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

    storage.commit()


@cli.command(help='Archive account')
@click.option('-a', '--account_name', type=str)
@click.pass_context
async def archive(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

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
@click.option('-a', '--account_name', type=str, default='Archive')
@click.pass_context
async def create_account(
    ctx: click.Context,
    account_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        bluecoins_storage.create_account(account_name, account_currency)


@cli.command(help='Add label to all account transactions')
@click.option('-a', '--account_name', type=str)
@click.option('-l', '--label_name', type=str)
@click.pass_context
async def add_label(
    ctx: click.Context,
    account_name: str,
    label_name: str,
) -> None:
    conn = open_copy(ctx.obj['path'])

    bluecoins_storage = BluecoinsStorage(conn)

    with transaction(conn) as conn:

        account_id = bluecoins_storage.get_account_id(account_name)
        bluecoins_storage.add_label(account_id, label_name)
