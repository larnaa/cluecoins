"""Module with queries to the Bluecoins database."""

import shutil
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection
from sqlite3 import Cursor
from sqlite3 import connect
from typing import Any
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
    conn.execute(
        'UPDATE SETTINGSTABLE SET defaultSettings = ? WHERE settingsTableID = "1";',
        (base_currency,),
    )


def iter_transactions(conn: Connection) -> Iterator[tuple[datetime, int, Decimal, str, Decimal]]:
    for row in conn.cursor().execute(
        'SELECT date, transactionsTableID, conversionRateNew, transactionCurrency, amount FROM TRANSACTIONSTABLE ORDER BY date DESC'
    ):
        date, id_, rate, currency, amount = row
        date = datetime.fromisoformat(date)
        rate = Decimal(str(rate))
        currency = currency.replace('USDT', 'USD')
        amount = Decimal(str(amount)) / 1000000
        yield date, id_, rate, currency, amount


def update_transaction(conn: Connection, id_: int, rate: Decimal, amount: Decimal) -> None:
    int_amount = int(amount * 1000000)
    conn.execute(
        'UPDATE TRANSACTIONSTABLE SET conversionRateNew = ?, amount = ? WHERE transactionsTableID = ?',
        (str(rate), int_amount, id_),
    )


def iter_accounts(conn: Connection) -> Iterator[tuple[int, str, Decimal]]:
    for row in conn.cursor().execute(
        'SELECT accountsTableID, accountCurrency, accountConversionRateNew FROM ACCOUNTSTABLE;'
    ):
        id_, currency, rate = row
        # FIXME: hardcode
        currency = currency.replace('USDT', 'USD')
        rate = Decimal(str(rate))
        yield id_, currency, rate


def update_account(conn: Connection, id_: int, rate: Decimal) -> None:
    conn.execute(
        'UPDATE ACCOUNTSTABLE SET accountConversionRateNew = ? WHERE accountsTableID = ?',
        (str(rate), id_),
    )


def find_account(conn: Connection, account_name: str) -> Any:
    account = conn.cursor().execute(
        'SELECT * FROM ACCOUNTSTABLE WHERE accountName = ?',
        (account_name,),
    )
    return account.fetchone()


def get_account_list(conn: Connection) -> list[Any]:
    account = conn.cursor().execute(
        'SELECT accountName, accountConversionRateNew FROM ACCOUNTSTABLE',
    )
    return account.fetchall()


def find_account_transactions_id(conn: Connection, account_id: int) -> Cursor:
    return conn.execute(
        'SELECT transactionsTableID FROM TRANSACTIONSTABLE WHERE accountID = ?',
        (account_id,),
    )


def add_label_to_transaction(conn: Connection, label_name: str, transaction_id: int) -> None:
    conn.execute(
        'INSERT INTO LABELSTABLE(labelName,transactionIDLabels) VALUES(?, ?)',
        (label_name, transaction_id),
    )


def get_base_currency(conn: Connection) -> Any:
    base_currency = conn.execute('SELECT defaultSettings FROM SETTINGSTABLE WHERE settingsTableID = 1;')
    return base_currency.fetchone()[0]


def create_new_account(conn: Connection, account_name: str, account_currency: str) -> None:
    # TODO: make variables mutable - accountTypeID and accountConversionRateNew (type: asset, rate: n/a)
    conn.execute(
        'INSERT INTO ACCOUNTSTABLE(accountName, accountTypeID, accountCurrency, accountConversionRateNew) \
            VALUES(?, 2, ?, 1)',
        (account_name, account_currency),
    )


def move_transactions_to_account(conn: Connection, account_id_old: int, account_id_new: int) -> None:
    conn.execute(
        'UPDATE TRANSACTIONSTABLE SET accountID = ? WHERE accountID = ?',
        (account_id_new, account_id_old),
    )
    conn.execute(
        'UPDATE TRANSACTIONSTABLE SET accountPairID = ? WHERE accountPairID = ?',
        (account_id_new, account_id_old),
    )


def delete_account(conn: Connection, account_id: int) -> None:
    conn.execute(
        'DELETE FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
        (account_id,),
    )
