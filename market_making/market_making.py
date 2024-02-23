from concurrent.futures import ThreadPoolExecutor
from traceback import format_exc
from rit import *

import requests
from time import sleep
import sys
import json
import signal

X_API_KEY = 'FPPGZ41T'
MIN_SPREAD = 0.07

# handles shutdown when CTRL+C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

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

        #automatic private tender offer *MOST IMPORTANT

        # every order or every few orders, reassign my spread number to be something else
        # 0.3 to 0.8 maybe..., dont keep it a constant
        # currencies
            # either entirely avoid. or work more deeply to improve handling currency orders
            #currency is 
        
        """
            every time i get a tender offer, 



                consider

                put a bunch of limit orders, like the commodities chimp strat


                try the chimp strat like the commodities case, limit order



                        be unpredicable, other ppl will know everything by the book, they try to profit off ur mistakes, so be random constants and be unpredictable

                    liquid everything after every 6 ticks, cancel position on everything to 0


                    
        """

        if spread < MIN_SPREAD:
            continue

        bid_quantity = min(max_trade_size, max_trade_size - position)
        ask_quantity = min(max_trade_size, max_trade_size + position)
        # make bid_quantity == ask_quantity?

        # min(max_trade_size, )

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

def handle_tenders(rit):
    tenders = rit.get_tenders()
    for tender in tenders:
        # Implement your decision logic here. Example:
        # Check if the tender price is favorable compared to the current market price
        market_price = rit.get_securities(ticker=tender['ticker'])[0].last_price
        if tender['price'] >= market_price * 1.05:  # Example criterion
            try:
                rit.post_tenders(tender['tender_id'], price=tender['price'])
                print(f"Accepted tender {tender['tender_id']} at price {tender['price']}")
            except Exception as e:
                print(f"Error accepting tender {tender['tender_id']}: {e}")
        else:
            try:
                rit.delete_tenders(tender['tender_id'])
                print(f"Declined tender {tender['tender_id']}")
            except Exception as e:
                print(f"Error declining tender {tender['tender_id']}: {e}")


def main():
    rit = RIT(X_API_KEY)

    securities = rit.get_securities()
    executor = ThreadPoolExecutor()
    futures = []

    for security in securities:
        if security.type == Security.Type.STOCK:
            futures.append(executor.submit(make_market, rit, security.ticker))

    # Add tender handling
    futures.append(executor.submit(handle_tenders, rit))

    for future in futures:
        future.result()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()