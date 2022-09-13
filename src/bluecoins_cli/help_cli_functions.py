from msilib.schema import Class
from sqlite3 import Connection

from bluecoins_cli.database import find_account
from bluecoins_cli.database import create_new_account
from bluecoins_cli.database import find_account_transactions_id
from bluecoins_cli.database import add_label_to_transaction


class DB:

    def create_account(conn: Connection, account_name: str, account_currency: str) -> None:
        if find_account(conn, account_name) is None:
            create_new_account(conn, account_name, account_currency)


    def get_account_id(conn: Connection, account_name: str) -> int:
        account_info = find_account(conn, account_name)
        return account_info[0]


    def add_label(conn: Connection, account_id: int, label_name: str) -> None:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in find_account_transactions_id(conn, account_id):
            transaction_id = transaction_id_tuple[0]
            add_label_to_transaction(conn, label_name, transaction_id)