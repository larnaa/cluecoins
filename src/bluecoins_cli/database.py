import shutil
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection
from sqlite3 import connect
from typing import Iterator


def open_copy(path: str, postfix: str = '.new') -> Connection:
    if not path.endswith('.fydb'):
        raise Exception('wrong extension')
    new_path = path.replace('.fydb', f'{postfix}.fydb')
    shutil.copyfile(path, new_path)
    return connect(new_path)


@contextmanager
def transaction(conn: Connection) -> Iterator[Connection]:
    yield conn
    conn.commit()


def set_base_currency(conn: Connection, base_currency: str) -> None:
    conn.execute(f"UPDATE SETTINGSTABLE SET defaultSettings = '{base_currency}' WHERE settingsTableID = '1';")


def iter_transactions(conn: Connection) -> Iterator[tuple[datetime, int, Decimal, str, Decimal]]:
    for row in conn.cursor().execute(
        "select date, transactionsTableID, conversionRateNew, transactionCurrency, amount from TRANSACTIONSTABLE ORDER BY date DESC"
    ):
        date, id_, rate, currency, amount = row
        date = datetime.fromisoformat(date)
        rate = Decimal(str(rate))
        currency = currency.replace('USDT', 'USD')
        amount = Decimal(str(amount)) / 1000000
        yield date, id_, rate, currency, amount


def update_transaction(conn: Connection, id_: int, rate: Decimal, amount: Decimal) -> None:
    int_amount = int(amount * 1000000)
    conn.execute(f"UPDATE TRANSACTIONSTABLE SET conversionRateNew = {rate}, amount = {int_amount} WHERE transactionsTableID = {id_};")


def iter_accounts(conn: Connection) -> Iterator[tuple[int, str, Decimal]]:
    for row in conn.cursor().execute("SELECT accountsTableID, accountCurrency, accountConversionRateNew FROM ACCOUNTSTABLE;"):
        id_, currency, rate = row
        currency = currency.replace('USDT', 'USD')
        rate = Decimal(str(rate))
        yield id_, currency, rate


def update_account(conn: Connection, id_: int, rate: Decimal) -> None:
    conn.execute(f"UPDATE ACCOUNTSTABLE SET accountConversionRateNew = '{rate}' WHERE accountsTableID = {id_};")

def create_archive_account(conn: Connection) -> None:
    conn.execute("INSERT into ACCOUNTSTABLE(accountName) values('Archive');")


def find_account(conn: Connection, account_name: str) -> tuple:
    account = conn.cursor().execute(f"SELECT * FROM ACCOUNTSTABLE WHERE ACCOUNTSTABLE.accountName='{account_name}';")
    return account.fetchone()
