import shutil
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from sqlite3 import Connection
from sqlite3 import Cursor
from sqlite3 import connect
from typing import Any
from typing import Iterator
from unicodedata import category


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
    conn.execute(
        f"UPDATE TRANSACTIONSTABLE SET conversionRateNew = {rate}, amount = {int_amount} WHERE transactionsTableID = {id_};"
    )


def iter_accounts(conn: Connection) -> Iterator[tuple[int, str, Decimal]]:
    for row in conn.cursor().execute(
        "SELECT accountsTableID, accountCurrency, accountConversionRateNew FROM ACCOUNTSTABLE;"
    ):
        id_, currency, rate = row
        currency = currency.replace('USDT', 'USD')
        rate = Decimal(str(rate))
        yield id_, currency, rate


def update_account(conn: Connection, id_: int, rate: Decimal) -> None:
    conn.execute(f"UPDATE ACCOUNTSTABLE SET accountConversionRateNew = '{rate}' WHERE accountsTableID = {id_};")


def find_account(conn: Connection, account_name: str) -> Any:
    account = conn.cursor().execute(f"SELECT * FROM ACCOUNTSTABLE WHERE ACCOUNTSTABLE.accountName='{account_name}';")
    return account.fetchone()


def find_account_transactions_id(conn: Connection, account_id: int) -> Cursor:
    return conn.execute(
        f"SELECT transactionsTableID FROM TRANSACTIONSTABLE WHERE TRANSACTIONSTABLE.accountID == {account_id};"
    )


def add_label_to_transaction(conn: Connection, label_name: str, transaction_id: int) -> None:
    conn.execute(f"INSERT INTO LABELSTABLE(labelName,transactionIDLabels) VALUES('{label_name}', {transaction_id});")


def get_base_currency(conn: Connection) -> Any:
    base_currency = conn.execute('SELECT defaultSettings FROM SETTINGSTABLE WHERE SETTINGSTABLE.settingsTableID = 1;')
    return base_currency.fetchone()[0]


def create_new_account(conn: Connection, account_name: str, account_currency: str) -> None:
    # TODO: make variables mutable - accountTypeID and accountConversionRateNew (type: asset, rate: n/a)
    conn.execute(
        f'INSERT into ACCOUNTSTABLE(accountName, accountTypeID, accountCurrency, accountConversionRateNew) \
            VALUES("{account_name}", 2, "{account_currency}", 1);'
    )


def move_transactions_to_account(conn: Connection, account_id_old: int, account_id_new: int) -> None:
    conn.execute(f"UPDATE TRANSACTIONSTABLE SET accountID = {account_id_new} WHERE accountID == {account_id_old};")
    conn.execute(f"UPDATE TRANSACTIONSTABLE SET accountPairID = {account_id_new} WHERE accountPairID == {account_id_old};")


def delete_account(conn: Connection, account_id: int) -> None:
    conn.execute(f"DELETE FROM ACCOUNTSTABLE WHERE accountsTableID = {account_id};")


class DBConnection:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def create_account(self, account_name: str, account_currency: str) -> None:
        if find_account(self.conn, account_name) is None:
            create_new_account(self.conn, account_name, account_currency)

    def get_account_id(self, account_name: str) -> int:
        # TODO: add error - if account not found
        account_info = find_account(self.conn, account_name)
        return int(account_info[0])

    def add_label(self, account_id: int, label_name: str) -> Any:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in find_account_transactions_id(self.conn, account_id):
            print(transaction_id_tuple)
            transaction_id = transaction_id_tuple[0]
            add_label_to_transaction(self.conn, label_name, transaction_id)

"""
    def change_account(self, account_id_new: int, account_id_old: int):

        transfer_group_id=1
        categoryID = 3
        
        for transaction_id_tuple in find_account_transactions_id(self.conn, account_id):
            if categoryID == 3:
                move_transactions_to_account(self.conn, account_id_old, account_id_new)

                move_pair_trnsfer_transaction_to_account(self.conn, transfer_group_id, account_id_new)



        #if categoryID=3:
            #- change: accountID=accountNewID
            #- find secondary transaction where transferGroupID same
            #- change: accountPairID=accountNewID
        
        move_transactions_to_account(self, account_id_new, account_id_old)
"""