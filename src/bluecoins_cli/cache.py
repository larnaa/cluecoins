from datetime import datetime
from decimal import Decimal

from aiohttp import ClientSession

from bluecoins_cli.storage import Storage


class QuoteCache:
    def __init__(self, storage: Storage) -> None:
        self._storage = storage

    async def _fetch_quotes(
        self,
        date: datetime,
        base_currency: str,
        quote_currency: str,
    ) -> None:
        # FIXME: Context manager
        async with ClientSession('https://api.exchangerate.host') as session:
            response = await session.get(
                url='/timeseries',
                params={
                    # FIXME: Overkill
                    'start_date': datetime(date.year, 1, 1).strftime('%Y-%m-%d'),
                    'end_date': datetime(date.year, 12, 31).strftime('%Y-%m-%d'),
                    'base': base_currency,
                    'symbols': [quote_currency],
                },
            )
            response_json = await response.json()
            for quote_date, items in response_json['rates'].items():
                for quote_currency, price in items.items():
                    self._storage.add_quote(
                        datetime.strptime(quote_date, '%Y-%m-%d'),
                        base_currency,
                        quote_currency,
                        Decimal(str(price)),
                    )

    # FIXME: Cache me
    async def get_price(
        self,
        date: datetime,
        base_currency: str,
        quote_currency: str,
    ) -> Decimal:
        if base_currency == quote_currency:
            return Decimal('1')

        price = self._storage.get_quote(date, base_currency, quote_currency)
        if not price:
            await self._fetch_quotes(date, base_currency, quote_currency)
            price = self._storage.get_quote(date, base_currency, quote_currency)

        if not price:
            raise Exception(f'No quote for {date} {base_currency} {quote_currency}')

        return price
