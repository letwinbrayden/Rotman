import util
from time import sleep

def get_news(session):
    return session.get('http://localhost:9999/v1/news?limit=1').json()

def parse_news(news):
    if news is None:
        return
    print(news)
    headline = news['headline']
    first_letter = headline[0]
    if (first_letter == 'W'):
        headline = headline.split(" ")
        actual_stock = headline[4]
        actual_qty = headline[5]
        forecast_stock = headline[10]
        forecast_qty = headline[11]
        return {
            'ALPHA_BETA': actual_stock,
            'GAMMA_BETA': actual_qty,
            'THETA_BETA': forecast_stock
        }
    else:
        return

def interpret_news(news):
    if news is None:
        return 
    actual_stock = news['actual_stock']
    actual_qty = news['actual_qty']
    forecast_stock = news['forecast_stock']
    forecast_qty = news['forecast_qty']
    actual_qty = int(actual_qty)
    forecast_qty = int(forecast_qty)
    # build build
    if ((actual_stock == 'BUILD') and (forecast_stock == 'BUILD')):
        dif = actual_qty - forecast_qty
        price_shock = dif / 10
        potential_profit = round(price_shock * 100 * 1_000 * -1)
        print('price-shock: ' + str(price_shock))
        print('potential-profit: ' + str(potential_profit))
        print('build-build-dif: ' + str(dif))
        if (actual_qty > forecast_qty):
            return { 'trade_decision': 'SELL', 'price_shock': price_shock }
        elif (actual_qty == forecast_qty):
            return { 'trade_decision': 'EQUAL', 'price_shock': price_shock }
        else:
            return { 'trade_decision': 'BUY', 'price_shock': price_shock }
    # draw build
    elif ((actual_stock == 'DRAW') and (forecast_stock == 'BUILD')):
        dif = (actual_qty * -1) - forecast_qty
        price_shock = dif / 10
        potential_profit = round(price_shock * 100 * 1000 * -1)
        print('price-shock: ' + str(price_shock))
        print('potential-profit: ' + str(potential_profit))
        print('draw-build-dif: ' + str(dif))
        return { 'trade_decision': 'BUY', 'price_shock': price_shock * -1 }
    # build draw
    elif ((actual_stock == 'BUILD') and (forecast_stock == 'DRAW')):
        dif = actual_qty - (forecast_qty * -1)
        price_shock = dif / 10
        potential_profit = round(price_shock * 100 * 1000 * -1)
        print('price-shock: ' + str(price_shock))
        print('potential-profit: ' + str(potential_profit))
        print('build-draw-dif: ' + str(dif))
        return { 'trade_decision': 'SELL', 'price_shock': price_shock }
    # draw draw
    else:
        dif = actual_qty - forecast_qty
        price_shock = dif / 10
        potential_profit = round(price_shock * 100 * 1000)
        print('price-shock: ' + str(price_shock))
        print('potential-profit: ' + str(potential_profit))
        print('draw-draw-dif: ' + str(dif))        
        if (actual_qty > forecast_qty):
            return { 'trade_decision': 'BUY', 'price_shock': price_shock }
        elif (actual_qty == forecast_qty):
            return { 'trade_decision': 'EQUAL', 'price_shock': price_shock }
        else:
            return { 'trade_decision': 'SELL', 'price_shock': price_shock }

def place_order(session, ticker, qty, trade_decision):
    storage_ticker = 'ALPHA'
    futures_ticker = 'ALPHA'
    orders_placed = 0
    if (trade_decision is None):
        return
    while trade_decision['trade_decision'] == 'BUY' and orders_placed < 7:
        util.lease_storage(session, storage_ticker)
        sleep(0.5)
        util.place_mkt_buy_order(session, ticker, qty)
        orders_placed += 1
    while trade_decision['trade_decision'] == 'SELL' and orders_placed < 7:
        util.place_mkt_sell_order(session, futures_ticker, qty)
        orders_placed += 1
        sleep(0.5)

def reset_position(session, trade_decision):
    if (trade_decision is None):
        return
    orders_placed = 0
    if (trade_decision['trade_decision'] == 'BUY'):
        ticker = 'ALPHA'
        quantity = 10
        price_shock = trade_decision['price_shock']
        print('price_shock: ' + str(price_shock))
        spot = session.get(f'http://localhost:9999/v1/securities?ticker={ticker}').json()[0]
        spot_price = spot['last']
        old_spot_price = spot_price
        while spot_price < ((old_spot_price + (price_shock * 0.75))):
            print('spot-price: ' + str(spot_price))
            spot_price_plus_shock = (old_spot_price + (price_shock * 0.7))
            print('spot-price-plus-shock: ' + str(spot_price_plus_shock))
            if (spot_price >= (old_spot_price + (price_shock * 0.7))):
                while orders_placed < 7:
                    util.place_mkt_sell_order(session, ticker, quantity)
                    orders_placed += 1
                    sleep(1)
            updated_spot = session.get(f'http://localhost:9999/v1/securities?ticker={ticker}').json()[0]
            sleep(1)
            spot_price = updated_spot['last']
            print(spot_price)

    elif (trade_decision['trade_decision'] == 'SELL'):
        ticker = 'ALPHA'
        quantity = 10
        price_shock = trade_decision['price_shock']
        print('price_shock: ' + str(price_shock))
        futures = session.get(f'http://localhost:9999/v1/securities?ticker={ticker}').json()[0]
        futures_price = futures['last']
        old_futures_price = futures_price
        while futures_price > (old_futures_price - (price_shock * 0.75)):
            print('futres-price: ' + str(futures_price))
            futures_price_minus_shock = (old_futures_price - (price_shock * 0.7))
            print('futures-price-minus-shock: ' + str(futures_price_minus_shock))
            if (futures_price <= (old_futures_price - (price_shock * 0.7))):
                while orders_placed < 7:
                    util.place_mkt_buy_order(session, ticker, quantity)
                    orders_placed += 1
                    sleep(1)
            updated_futures = session.get(f'http://localhost:9999/v1/securities?ticker={ticker}').json()[0]
            sleep(1)
            futures_price = updated_futures['last']
            print(futures_price)
    
def main():
    session = util.open_session()
    tick = util.get_tick(session)
    ticker = 'ALPHA'
    quantity = 10
    old_news_id = -1
    while tick >= 0 and tick <= 600:
        news = get_news(session)[0]
        print(get_news(session)[0])
        if news['headline'] != 'Welcome to the RITC 2024 ALGO CAPM Forecasting Case':
            if (news['news_id'] == old_news_id):
                news = None
            news_results = parse_news(news)
            trade_decsion = interpret_news(news_results)
            print(trade_decsion)
            place_order(session, ticker, quantity, trade_decsion)
            sleep(1)
            reset_position(session, trade_decsion)
            if news is not None:
                old_news_id = news['news_id']
        tick = util.get_tick(session)
        print('tick: ' + str(tick))

main()