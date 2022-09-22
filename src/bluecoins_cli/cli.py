import logging
import os
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

import asyncclick as click
import xdg

from bluecoins_cli.cache import QuoteCache
from bluecoins_cli.database import DBConnection
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

logging.basicConfig(level=logging.DEBUG)


def q(v: Decimal, prec: int = 2) -> Decimal:
    return v.quantize(Decimal(f'0.{prec * "0"}'))


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

    dbconnection = DBConnection(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        dbconnection.create_account('Archive', account_currency)

        # add labels: cli_archive, cli_%name_acc_old%
        account_id = dbconnection.get_account_id(account_name)

        dbconnection.add_label(account_id, 'cli_archive')
        dbconnection.add_label(account_id, f'cli_{account_name}')

        # FIXME: some transactions "transfer between accounts" still have a deleted account after move transactions.
        # move transactions to account Archive
        account_archive_id = dbconnection.get_account_id('Archive')
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

    dbconnection = DBConnection(conn)

    with transaction(conn) as conn:

        account_currency = get_base_currency(conn)
        dbconnection.create_account(account_name, account_currency)


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

    dbconnection = DBConnection(conn)

    with transaction(conn) as conn:

        account_id = dbconnection.get_account_id(account_name)
        dbconnection.add_label(account_id, label_name)
