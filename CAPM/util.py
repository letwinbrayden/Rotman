import requests
from time import sleep
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

def open_session():
    API_KEY = {'X-API-key': '91V2OTC7'}
    session = requests.Session()
    session.headers.update(API_KEY)
    return session

def get_tick(session):
    response = session.get(f'http://localhost:9999/v1/case')
    case_info = response.json()
    tick = case_info['tick']
    return tick

def get_news(session):
    return session.get('http://localhost:9999/v1/news?limit=12').json()

def get_bid_orders(session, ticker):
    response = session.get(f'http://localhost:9999/v1/securities/book?ticker={ticker}')
    order_book = response.json()
    bids = order_book['bids']
    bids_clean = []
    highest_bid = -1
    for bid in bids:
        if bid['price'] >= highest_bid:
            highest_bid = bid['price']
        bid_clean = {
            'price': bid['price'],
            'quantity': bid['quantity']
        }
        bids_clean.append(bid_clean)
    return [bids_clean, highest_bid]

def get_ask_orders(session, ticker):
    response = session.get(f'http://localhost:9999/v1/securities/book?ticker={ticker}')
    order_book = response.json()
    asks = order_book['asks']
    asks_clean = []
    lowest_ask = 100000000
    for ask in asks:
        if ask['price'] <= lowest_ask:
            lowest_ask = ask['price']
        ask_clean = {
            'price': ask['price'],
            'quantity': ask['quantity']
        }
        asks_clean.append(ask_clean)
    return [asks_clean, lowest_ask]

def get_position(session, ticker):
    response = session.get('http://localhost:9999/v1/securities')
    securities = response.json()
    position = -1
    for security in securities:
        if security['ticker'] == ticker:
            position = security['position']
    return position

def get_prices(session):
    response = session.get('http://localhost:9999/v1/securities')
    securities = response.json()
    prices = {}
    for security in securities:
        prices[security['ticker']] = security['last']
    return prices

def unrealized_pft(session):
    response = session.get('http://localhost:9999/v1/securities')
    securities = response.json()
    unrealized_pft = {}
    for security in securities:
        unrealized_pft[security['ticker']] = security['unrealized']
    return unrealized_pft

def remove_closed_orders(orders):
    open_orders = []
    for order in orders:
        if (order['status'] == 'OPEN'):
            open_orders.append(order)
    return open_orders

def get_orders_to_cancel(orders, current_tick):
    orders_to_cancel = []
    max_open_time = 4
    for order in orders:
        if (order['status'] == 'OPEN' and (current_tick - order['tick'] > max_open_time)):
            orders_to_cancel.append(order)
    return orders_to_cancel

def cancel_orders(session, orders_to_cancel):
    for order in orders_to_cancel:
        order_id = order['id']
        res = session.delete(f'http://localhost:9999/v1/orders/{order_id}')
        if (res.status_code == 200):
            return True
    return False

def place_mkt_buy_order(session, ticker, qty):
    res = session.post(f'http://localhost:9999/v1/orders?ticker={ticker}&type=MARKET&quantity={qty}&action=BUY')
    #print(res.json())

def place_mkt_sell_order(session, ticker, qty):
    res = session.post(f'http://localhost:9999/v1/orders?ticker={ticker}&type=MARKET&quantity={qty}&action=SELL')
    #print(res.json())

def main():
    print()
if __name__ == "__main__":
    main()