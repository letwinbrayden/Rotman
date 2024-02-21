# This is a python example algorithm using REST API for the RIT ALGO2 Case
import signal
import requests
from time import sleep
import sys

# This class definition allows us to print error messages and stop the program
class ApiException(Exception): 
    pass

# This signal handler allows for a graceful shutdown when CTRL+C is pressed
def signal_handler(signum, frame):
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    shutdown = True

# Set your API key to authenticate to the RIT client
API_KEY = {'X-API-Key': 'XC904YR5'}
shutdown = False

# SETTINGS
# How long to wait after submitting buy or sell orders
SPEEDBUMP = 0.5
# Maximum number of shares to purchase each order
MAX_VOLUME = 5000
# Maximum number of orders we can submit
MAX_ORDERS = 5
# Allowed spread before we sell or buy shares
SPREAD = 0.05

# This helper method returns the current 'tick' of the running case.
def get_tick(session):
    resp = session.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick']
    raise ApiException('Authorization error. Please check API key.')

# This helper method returns the bid and ask first row for a given security.
def ticker_bid_ask(session, ticker):
    payload = {'ticker': ticker}
    resp = session.get('http://localhost:9999/v1/securities/book', params=payload)
    if resp.ok:
        book = resp.json()
        return book['bids'][0]['price'], book['asks'][0]['price']
    raise ApiException('Authorization error. Please check API key.')

# This helper method returns information about all the open sell orders
def open_sells(session):
    resp = session.get('http://localhost:9999/v1/orders?status=OPEN')
    if resp.ok:
        open_sells_volume = 0  # total combined volume of all open sells
        ids = []  # all open sell ids
        prices = []  # all open sell prices
        order_volumes = []  # all open sell volumes
        volume_filled = []  # volume filled for each open sell order

        open_orders = resp.json()
        for order in open_orders:
            if order['action'] == 'SELL':
                volume_filled.append(order['quantity_filled'])
                order_volumes.append(order['quantity'])
                open_sells_volume += order['quantity']
                prices.append(order['price'])
                ids.append(order['order_id'])

    return volume_filled, open_sells_volume, ids, prices, order_volumes

# This helper method returns information about all open buy orders
def open_buys(session):
    resp = session.get('http://localhost:9999/v1/orders?status=OPEN')
    if resp.ok:
        open_buys_volume = 0  # total combined volume of all open buys
        ids = []  # all open buy ids
        prices = []  # all open buy prices
        order_volumes = []  # all open buy volumes
        volume_filled = []  # volume filled of each open buy order

        open_orders = resp.json()
        for order in open_orders:
            if order['action'] == 'BUY':
                open_buys_volume += order['quantity']
                volume_filled.append(order['quantity_filled'])
                order_volumes.append(order['quantity'])
                prices.append(order['price'])
                ids.append(order['order_id'])

    return volume_filled, open_buys_volume, ids, prices, order_volumes

# This helper method will buy and sell the maximum number of shares
def buy_sell(session, sell_price, buy_price):
    for i in range(MAX_ORDERS):
        session.post('http://localhost:9999/v1/orders', params={'ticker': 'ALGO',
                                                               'type': 'LIMIT',
                                                               'quantity': MAX_VOLUME,
                                                               'price': sell_price,
                                                               'action': 'SELL'})
        session.post('http://localhost:9999/v1/orders', params={'ticker': 'ALGO',
                                                               'type': 'LIMIT',
                                                               'quantity': MAX_VOLUME,
                                                               'price': buy_price,
                                                               'action': 'BUY'})

# This helper method re-orders all open buys or sells
def re_order(session, number_of_orders, ids, volumes_filled, volumes, price, action):
    for i in range(number_of_orders):
        id = ids[i]
        volume = volumes[i]
        volume_filled = volumes_filled[i]
        # If the order is partially filled.
        if volume_filled != 0:
            volume = MAX_VOLUME - volume_filled
        # Delete then re-purchase.
        deleted = session.delete(f'http://localhost:9999/v1/orders/{id}')
        if deleted.ok:
            session.post('http://localhost:9999/v1/orders', params={
                'ticker': 'ALGO', 'type': 'LIMIT', 'quantity': volume, 'price': price, 'action': action})

def main():
    # Instantiate variables about all the open buy orders
    buy_ids = []  # order ids
    buy_prices = []  # order prices
    buy_volumes = []  # order volumes
    volume_filled_buys = []  # amount of volume filled for each order
    open_buys_volume = 0  # combined volume from all open buy orders

    # Instantiate variables about all the open sell orders
    sell_ids = []
    sell_prices = []
    sell_volumes = []
    volume_filled_sells = []
    open_sells_volume = 0

    # Instantiated variables when just one side of the book has been completely filled
    single_side_filled = False
    single_side_transaction_time = 0

    # Creates a session to manage connections and requests to the RIT Client
    with requests.Session() as s:
        s.headers.update(API_KEY)
        tick = get_tick(s)

        # While the time is between 5 and 295, do the following
        while tick > 5 and tick < 295 and not shutdown:
            # Update information about the case
            volume_filled_sells, open_sells_volume, sell_ids, sell_prices, sell_volumes = open_sells(s)
            volume_filled_buys, open_buys_volume, buy_ids, buy_prices, buy_volumes = open_buys(s)
            bid_price, ask_price = ticker_bid_ask(s, 'ALGO')




            # check if you have 0 open orders
            if (open_sells_volume == 0 and open_buys_volume == 0):
                # both sides are filled now
                single_side_filled = False 

            # calculate the spread between the bid and ask prices
            bid_ask_spread = ask_price - bid_price 

            # set the prices
            sell_price = ask_price
            buy_price = bid_price 

            # the calculated spread is greater or equal to our set spread
            if (bid_ask_spread >= SPREAD):
                # buy and sell the maximum number of shares
                buy_sell(s, sell_price, buy_price)
                sleep(SPEEDBUMP)

            # there are outstanding open orders
            else:
                # one side of the book has no open orders
                if (not single_side_filled and (open_buys_volume == 0 or open_sells_volume == 0)):
                    single_side_filled = True
                    single_side_transaction_time = tick 

                # ask side has been completely filled
                if (open_sells_volume == 0):
                    # current buy orders are at the top of the book
                    if (buy_price == bid_price):
                        continue  # next iteration of loop

                    # it's been more than 3 seconds since a single side has been completely filled
                    elif (tick - single_side_transaction_time >= 3):
                        # calculate the potential profits you can make
                        next_buy_price = bid_price + .01
                        potential_profit = sell_price - next_buy_price - .02 

                        # potential profit is greater than or equal to a cent or it's been more than 6 seconds
                        if (potential_profit >= .01 or tick - single_side_transaction_time >= 6):
                            action = 'BUY'
                            number_of_orders = len(buy_ids)
                            buy_price = bid_price + .01
                            price = buy_price
                            ids = buy_ids
                            volumes = buy_volumes
                            volumes_filled = volume_filled_buys 

                            # delete buys and re-buy
                            re_order(s, number_of_orders, ids, volumes_filled, volumes, price, action)
                            sleep(SPEEDBUMP)
