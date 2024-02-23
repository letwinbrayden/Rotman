from concurrent.futures import ThreadPoolExecutor
from traceback import format_exc
from market_making.ritc import *
import requests
from time import sleep
import sys
import json
import signal
import random  # Import the random module

X_API_KEY = 'FPPGZ41T'

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

        # Random spread between 7 cents and 9 cents
        MIN_SPREAD = random.uniform(0.07, 0.09)  # *****random spread, 6 to 9 cents

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

"""
limit order function for a certain price, sleep for a little as possible
"""

#brayden down
def submit_limit_order(ticker, order_type, price, quantity):
    """
    Submits a limit order.
    
    :param ticker: Ticker symbol of the security.
    :param order_type: 'ask' for selling, 'bid' for buying.
    :param price: Price at which to place the order.
    :param quantity: Quantity of shares to trade.
    """
    order_action = ritc.Order.Action.BUY if order_type == 'bid' else ritc.Order.Action.SELL
    try:
        order = rit_client.post_orders(
            ticker=ticker,
            type=ritc.Order.Type.LIMIT,
            quantity=quantity,
            action=order_action,
            price=price
        )
        print(f"Limit order submitted: {order}")
    except Exception as e:
        print(f"Error submitting limit order: {e}")

def calculate_and_submit_orders(ticker_symbol, spread, quantity):
    """
    Calculates and submits limit orders based on the given ticker's bid and ask prices.
    
    :param ticker_symbol: Ticker symbol of the security.
    :param spread: Minimum spread to consider for placing orders.
    :param quantity: Quantity of shares to trade.
    """
    # Fetch current bid and ask prices
    ticker_data = rit_client.get_securities(ticker=ticker_symbol)
    ask = ticker_data.ask
    bid = ticker_data.bid
    mid = (ask + bid) / 2

    # Check if the conditions are met
    if (ask - mid) / 2 >= 0.01 and (mid - bid) / 2 >= 0.01:
        if (ask - bid) > spread:
            # Submit ask and bid limit orders
            submit_limit_order(ticker_symbol, 'ask', (ask + mid) / 2, quantity)
            submit_limit_order(ticker_symbol, 'bid', (bid + mid) / 2, quantity)
#brayden up

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