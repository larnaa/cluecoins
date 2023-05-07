"""Module with queries to the Bluecoins database."""

from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection
from sqlite3 import Cursor
from sqlite3 import connect
from typing import Any
from typing import Iterator


def connect_local_db(path: str) -> Connection:
    if not path.endswith('.fydb'):
        raise Exception('wrong extension')
    return connect(path)


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


def iter_accounts(
    conn: Connection, old_currency: str = 'USDT', new_currency: str = 'USD'
) -> Iterator[tuple[int, str, Decimal]]:
    for row in conn.cursor().execute(
        'SELECT accountsTableID, accountCurrency, accountConversionRateNew FROM ACCOUNTSTABLE;'
    ):
        id_, currency, rate = row
        currency = currency.replace(old_currency, new_currency)
        rate = Decimal(str(rate))
        yield id_, currency, rate


def update_account(conn: Connection, id_: int, rate: Decimal) -> None:
    conn.execute(
        'UPDATE ACCOUNTSTABLE SET accountConversionRateNew = ? WHERE accountsTableID = ?',
        (str(rate), id_),
    )


def find_account(conn: Connection, account_name: str, clue: bool = False) -> Any:
    table = 'ACCOUNTSTABLE'

    if clue:
        table = f'CLUE_{table}'

    account = conn.cursor().execute(
        f'SELECT * FROM {table} WHERE accountName = ?',
        (account_name,),
    )
    return account.fetchone()


def get_accounts_list(conn: Connection, clue: bool = False) -> list[Any]:
    table = 'ACCOUNTSTABLE'

    if clue:
        table = f'CLUE_{table}'

    account = conn.cursor().execute(
        f'SELECT accountName, accountConversionRateNew FROM {table}',
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


def delete_account(conn: Connection, account_id: int) -> None:
    conn.execute(
        'DELETE FROM ACCOUNTSTABLE WHERE accountsTableID = ?',
        (account_id,),
    )


def find_transactions_by_label(conn: Connection, label_name: str) -> list[tuple[int]]:
    transactions = conn.cursor().execute(
        'SELECT transactionIDLabels FROM LABELSTABLE where labelName = ?',
        (label_name,),
    )
    return transactions.fetchall()


def delete_label(conn: Connection, label_name: str) -> None:
    conn.execute(
        'DELETE FROM LABELSTABLE WHERE labelName = ?',
        (label_name,),
    )


def find_labels_by_transaction_id(conn: Connection, transaction_id: int) -> list[tuple[str]]:
    labels = conn.cursor().execute(
        'SELECT labelName FROM LABELSTABLE WHERE transactionIDLabels = ?',
        (transaction_id,),
    )
    return labels.fetchall()


def get_transactions_list(conn: Connection, account_id: int, revert: bool = False) -> list[tuple[int]]:
    table = 'TRANSACTIONSTABLE'

    if revert:
        table = f'CLUE_{table}'

    transactions = conn.cursor().execute(
        f'SELECT transactionsTableID FROM {table} WHERE accountID = {account_id}',
    )
    return transactions.fetchall()


def execute_command(conn: Connection, command: str) -> None:
    conn.cursor().execute(command)


def copy_data_to_table_by_id(conn: Connection, table: str, filter: str, id_: int, revert: bool = False) -> None:
    if revert is False:
        new_table = f'CLUE_{table}'
    else:
        new_table = table
        table = f'CLUE_{table}'

    conn.cursor().execute(f'INSERT INTO {new_table} SELECT * FROM {table} WHERE {filter} = {id_}')


def delete_data_by_id(conn: Connection, table: str, filter: str, id_: int, revert: bool = False) -> None:
    if revert:
        table = f'CLUE_{table}'
    conn.cursor().execute(f'DELETE FROM {table} WHERE {filter} = {id_}')
