from datetime import datetime
from decimal import Decimal

import requests

from cluecoins.storage import Storage


class QuoteCache:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    def _fetch_quotes(
        self,
        date: datetime,
        base_currency: str,
        quote_currency: str,
    ) -> None:
        """Getting quotes from the Exchangerate API and writing them to the local database"""

        latest_rates = requests.get(url='https://api.exchangerate.host/latest').json()['rates']
        if base_currency not in latest_rates or quote_currency not in latest_rates:
            raise Exception(f'No currency {base_currency} or {quote_currency} in response')

        response = requests.get(
            url='https://api.exchangerate.host/timeseries',
            params={
                # FIXME: Overkill
                'start_date': datetime(date.year, 1, 1).strftime('%Y-%m-%d'),
                'end_date': datetime(date.year, 12, 31).strftime('%Y-%m-%d'),
                'base': base_currency,
                'symbols': [quote_currency],
            },
        )
        response_json = response.json()
        for quote_date, items in response_json['rates'].items():
            for quote_currency, price in items.items():
                self._storage.add_quote(
                    datetime.strptime(quote_date, '%Y-%m-%d'),
                    base_currency,
                    quote_currency,
                    Decimal(str(price)),
                )

    # FIXME: Cache me
    def get_price(
        self,
        date: datetime,
        base_currency: str,
        quote_currency: str,
    ) -> Decimal:
        if base_currency == quote_currency:
            return Decimal('1')

        price = self._storage.get_quote(date, base_currency, quote_currency)
        if not price:
            self._fetch_quotes(date, base_currency, quote_currency)
            price = self._storage.get_quote(date, base_currency, quote_currency)

        if not price:
            raise Exception(f'No quote for {date} {base_currency} {quote_currency}')

        return price
