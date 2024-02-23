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

# ... [Other functions like submit_limit_order remain the same] ...

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

# ... [Rest of the calculate_and_submit_orders function and other parts remain unchanged] ...

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
