from concurrent.futures import ThreadPoolExecutor
from traceback import format_exc
from ritc import *
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

def submit_limit_order(ticker, order_type, price, quantity):
    """
    Submits a limit order.
    
    :param ticker: Ticker symbol of the security.
    :param order_type: 'ask' for selling, 'bid' for buying.
    :param price: Price at which to place the order.
    :param quantity: Quantity of shares to trade.
    """
    order_action = Order.Action.BUY if order_type == 'bid' else Order.Action.SELL
    try:
        order = rit_client.post_orders(
            ticker=ticker,
            type=Order.Type.LIMIT,
            quantity=quantity,
            action=order_action,
            price=price
        )
        print(f"Limit order submitted: {order}")
    except Exception as e:
        print(f"Error submitting limit order: {e}")

def fetch_current_price(rit, ticker):
    """
    Fetch the current market price for a given ticker.
    """
    securities = rit.get_securities(ticker=ticker)
    return securities[0].last

def is_offer_profitable(tender, current_price, margin=0.02):
    """
    Determines if a tender offer is profitable based on a conservative margin.
    """
    if tender.action == 'SELL':
        return tender.price > (current_price * (1 + margin))
    elif tender.action == 'BUY':
        return tender.price < (current_price * (1 - margin))
    return False

def handle_tender_offers(rit):
    """
    Handles all active tender offers conservatively.
    """
    try:
        active_tenders = rit.get_tenders()
    except Exception as e:
        print(f"Error fetching tenders: {e}")
        return

    for tender in active_tenders:
        try:
            current_price = fetch_current_price(rit, tender.ticker)
            if is_offer_profitable(tender, current_price):
                result = rit.post_tenders(tender.tender_id)
                print(f"Accepted offer on {tender.ticker}: {result}")
            else:
                print(f"Offer not profitable for {tender.ticker}")
        except Exception as e:
            print(f"Error handling tender offer for {tender.ticker}: {e}")

def calculate_and_submit_orders(rit, ticker):
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
        MIN_SPREAD = random.uniform(0.07, 0.09)

        if spread < MIN_SPREAD:
            continue

        bid_quantity = min(max_trade_size, max_trade_size - position)
        ask_quantity = min(max_trade_size, max_trade_size + position)

        if bid_quantity > 0:
            submit_limit_order(ticker, 'bid', bid, bid_quantity)

        if ask_quantity > 0:
            submit_limit_order(ticker, 'ask', ask, ask_quantity)


def main():
    rit = RIT(X_API_KEY)

    securities = rit.get_securities()
    executor = ThreadPoolExecutor()
    futures = []

    for security in securities:
        if security.type == Security.Type.STOCK:
            futures.append(executor.submit(calculate_and_submit_orders, rit, security.ticker))

    # Add tender handling
    futures.append(executor.submit(handle_tender_offers, rit))

    for future in futures:
        future.result()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
