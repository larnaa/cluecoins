from datetime import datetime
from decimal import Decimal
from pathlib import Path
from sqlite3 import Connection
from sqlite3 import connect
from typing import Any
from typing import Optional

import xdg

from bluecoins_cli import database as db


class Storage:
    def __init__(self) -> None:
        self._path = Path(xdg.xdg_data_home()) / 'bluecoins-cli' / 'bluecoins-cli.db'
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)
        self._db = connect(self._path)

    def init(self) -> None:
        self._db.execute(
            'CREATE TABLE IF NOT EXISTS quotes (date TEXT, base_currency TEXT, quote_currency TEXT, price REAL)'
        )

    def commit(self) -> None:
        self._db.commit()

    def get_quote(self, date: datetime, base_currency: str, quote_currency: str) -> Optional[Decimal]:
        date = datetime.strptime(datetime.strftime(date, '%Y-%m-%d'), '%Y-%m-%d')
        res = self._db.execute(
            'SELECT price FROM quotes WHERE date = ? AND base_currency = ? AND quote_currency = ?',
            (date, base_currency, quote_currency),
        ).fetchone()
        if res:
            return Decimal(str(res[0]))
        return None

    def add_quote(self, date: datetime, base_currency: str, quote_currency: str, price: Decimal) -> None:
        date = datetime.strptime(datetime.strftime(date, '%Y-%m-%d'), '%Y-%m-%d')
        if not self.get_quote(date, base_currency, quote_currency):
            self._db.execute(
                'INSERT INTO quotes (date, base_currency, quote_currency, price) VALUES (?, ?, ?, ?)',
                (date, base_currency, quote_currency, str(price)),
            )


class BluecoinsStorage:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def create_account(self, account_name: str, account_currency: str) -> None:
        if db.find_account(self.conn, account_name) is None:
            db.create_new_account(self.conn, account_name, account_currency)

    def get_account_id(self, account_name: str) -> int:
        account_info = db.find_account(self.conn, account_name)
        return int(account_info[0])

    def add_label(self, account_id: int, label_name: str) -> Any:
        # find all transation with ID account and add labels with id transactions to LABELSTABEL
        for transaction_id_tuple in db.find_account_transactions_id(self.conn, account_id):
            transaction_id = transaction_id_tuple[0]
            db.add_label_to_transaction(self.conn, label_name, transaction_id)