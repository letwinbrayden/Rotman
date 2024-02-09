from concurrent.futures import ThreadPoolExecutor
from traceback import format_exc

from requests import HTTPError
from ritc import Case, Order, RIT, Security

X_API_KEY = '78DZHH2V'
MIN_SPREAD = 0.07


def make_market(rit, ticker):
    while rit.get_case().status == Case.Status.ACTIVE:
        security = rit.get_securities(ticker=ticker)[0]
        position = security.position
        max_trade_size = security.max_trade_size
        book = rit.get_securities_book(ticker=ticker, limit=1)

        if not book.bids or not book.asks:
            continue

        bid = book.bids[0].price
        ask = book.asks[0].price
        spread = ask - bid

        if spread < MIN_SPREAD:
            continue

        bid_quantity = min(max_trade_size, max_trade_size - position)
        ask_quantity = min(max_trade_size, max_trade_size + position)

        if bid_quantity > 0:
            rit.post_commands_cancel(
                query=f'Ticker=\'{ticker}\' AND Price<{bid} AND Volume>0',
            )

            try:
                rit.post_orders(
                    True,
                    ticker=ticker,
                    type=Order.Type.LIMIT,
                    quantity=bid_quantity,
                    action=Order.Action.BUY,
                    price=bid,
                )
            except HTTPError as error:
                print(format_exc())
                print(error.response.json())
        else:
            rit.post_commands_cancel(query=f'Ticker=\'{ticker}\' AND Volume>0')

        if ask_quantity > 0:
            rit.post_commands_cancel(
                query=f'Ticker=\'{ticker}\' AND Price>{ask} AND Volume<0',
            )

            try:
                rit.post_orders(
                    True,
                    ticker=ticker,
                    type=Order.Type.LIMIT,
                    quantity=ask_quantity,
                    action=Order.Action.SELL,
                    price=ask,
                )
            except HTTPError as error:
                print(format_exc())
                print(error.response.json())
        else:
            rit.post_commands_cancel(query=f'Ticker=\'{ticker}\' AND Volume<0')


def main():
    rit = RIT(X_API_KEY)
    securities = rit.get_securities()
    executor = ThreadPoolExecutor()
    futures = []

    for security in securities:
        if security.type == Security.Type.STOCK:
            futures.append(executor.submit(make_market, rit, security.ticker))

    for future in futures:
        future.result()


if __name__ == '__main__':
    main()