from datetime import datetime
from decimal import Decimal
from typing import Any
from typing import Dict

from cluecoins.cache import QuoteCache
from cluecoins.storage import Storage


def test_fetch_quotes(initialization_storage: Storage) -> None:
    currency_info: Dict[str, Any] = {
        'date': datetime(2022, 7, 15),
        'base_currency': 'USD',
        'quote_currency': 'UYU',
    }

    cache = QuoteCache(initialization_storage)
    conn = initialization_storage.db
    cache._fetch_quotes(**currency_info)

    quote_data = conn.cursor().execute(
        'SELECT * FROM quotes',
    )

    expected_quote_data = len(quote_data.fetchall())

    assert expected_quote_data == 328


def test_get_price(initialization_storage: Storage) -> None:
    currency_info: Dict[str, Any] = {
        'date': datetime(2022, 7, 15),
        'base_currency': 'USD',
        'quote_currency': 'UYU',
    }

    cache = QuoteCache(initialization_storage)
    conn = initialization_storage.db

    expected_quote_price = cache.get_price(**currency_info)

    price = conn.cursor().execute(
        'SELECT * FROM quotes WHERE date = "2022-07-15 00:00:00"',
    )

    quote_price = price.fetchall()[0][3]

    assert expected_quote_price == Decimal(f'{quote_price}')
