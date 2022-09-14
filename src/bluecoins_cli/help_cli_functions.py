# from msilib.schema import Class
from sqlite3 import Connection
from typing import Any

from bluecoins_cli.database import add_label_to_transaction
from bluecoins_cli.database import create_new_account
from bluecoins_cli.database import find_account
from bluecoins_cli.database import find_account_transactions_id


class DBConnection:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def create_account(self, account_name: str, account_currency: str) -> None:
        if find_account(self.conn, account_name) is None:
            create_new_account(self.conn, account_name, account_currency)

    def get_account_id(self, account_name: str) -> int:
        account_info = find_account(self.conn, account_name)
        return int(account_info[0])

    def add_label(self, account_id: int, label_name: str) -> Any:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in find_account_transactions_id(self.conn, account_id):
            transaction_id = transaction_id_tuple[0]
            add_label_to_transaction(self.conn, label_name, transaction_id)
