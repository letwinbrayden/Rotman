import util
import statsmodels.api as sm
import numpy as np
from time import sleep

class Algo:

    def __init__(self):
        self.session = util.open_session()
        self.tickers = {"ALPHA": {"BETA": 1},
                        "GAMMA": {"BETA": 1}, 
                        "THETA": {"BETA": 1}}
        
        self.index_returns = []
        self.index_last_price = -1

        self.returns = {"ALPHA": [], "GAMMA": [], "THETA": []}
        self.last_prices = {"ALPHA": -1, "GAMMA": -1, "THETA": -1}
        self.portfolio = {"ALPHA": [], "GAMMA": [], "THETA": []}

    def start_session(self):
        print("Session Not Active.")
        while True:
            tick = util.get_tick(self.session)
            if tick >= 1:
                info = util.get_news(self.session)[-1]
                info = info['body'].split()
                self.riskfree = float(info[11].replace("%.", "")) / 100
                self.tickers['ALPHA']['BETA'] = float(info[31])
                self.tickers['GAMMA']['BETA'] = float(info[34])
                self.tickers['THETA']['BETA'] = float(info[37])
                self.news = info
                print("Session Active.")
                return

    def update_news(self):
        news = util.get_news(self.session)
        if news != self.news:
            self.news = news
            data = self.news[0]['body'].split()
            tick = int(data[6].replace(",",""))
            index_value = float(data[16][1:].replace(".",""))
            return [True, tick, index_value]
        return [False]
    
    def update_returns(self):
        prices = util.get_prices(self.session)
        if self.index_last_price == -1:
            self.index_returns.append(0)
        else:
            self.index_returns.append((prices["RITM"] - self.index_last_price) / self.index_last_price * 100)
        self.index_last_price = prices["RITM"]
        if len(self.index_returns) >= 500:
            self.index_returns.pop(0)

        for ticker in self.tickers:
            if self.last_prices[ticker] == -1:
                self.returns[ticker].append(0)
            else:
                self.returns[ticker].append((prices[ticker] - self.last_prices[ticker]) / self.last_prices[ticker])
            self.last_prices[ticker] = prices[ticker]
            if len(self.returns[ticker]) >= 500:
                self.returns[ticker].pop(0)
        return
        
    def place_order(self, ticker, qty, trade_decision):
        orders_placed = 0
        while trade_decision == 'BUY' and orders_placed < 7:
            util.place_mkt_buy_order(self.session, ticker, qty)
            orders_placed += 1
            sleep(0.1)
        while trade_decision == 'SELL' and orders_placed < 7:
            util.place_mkt_sell_order(self.session, ticker, qty)
            orders_placed += 1
            sleep(0.1)

    def calculate_market_return(self):
        mean_return = np.mean(self.index_returns)
        std_return = np.std(self.index_returns)
        num_simulations = 500
        scenarios = np.random.normal(mean_return, std_return, num_simulations)
        expected_return = np.mean(scenarios)
        return expected_return
    
    def calculate_value(self, ticker, market_return):
        return self.riskfree + (self.tickers[ticker]["BETA"] * (market_return - self.riskfree))
    
    def evaluate_value(self):
        for ticker in self.tickers:
            bids, highest_bid = util.get_bid_orders(self.session, ticker)
            asks, lowest_ask = util.get_ask_orders(self.session, ticker)
            market_return = self.calculate_market_return()
            capm = self.calculate_value(ticker, market_return)
            if self.last_prices[ticker] * (1 + capm) - 0.02 >= lowest_ask:
                self.place_order(ticker, 125, "BUY")
                self.portfolio[ticker].append({"STATUS": "BUY", "PRICE": lowest_ask})
            elif self.last_prices[ticker] * (1 + capm) + 0.02 <= highest_bid:
                self.place_order(ticker, 125, "SELL")
                self.portfolio[ticker].append({"STATUS": "SELL", "PRICE": highest_bid})
            if util.unrealized_pft(self.session)[ticker] >= 10000 or util.unrealized_pft(self.session)[ticker] <= -10000:
                    while util.get_position(self.session, ticker) > 100:
                        util.place_mkt_sell_order(self.session, ticker, 100)
                        sleep(0.1)
                    while util.get_position(self.session, ticker) < -1000:
                        util.place_mkt_buy_order(self.session, ticker, 100)
                        sleep(0.1)

    def calculate_new_beta(self):
        for ticker in self.tickers:
            X = sm.add_constant(self.index_returns)
            model = sm.OLS(self.returns[ticker], X)
            results = model.fit()
            new_beta_estimate = results.params[1]
            self.tickers[ticker]["BETA"] = new_beta_estimate



def main():
    algo = Algo()
    algo.start_session()
    tick = util.get_tick(algo.session)

    while tick >= 1 and tick <= 10:
        algo.update_returns()
        algo.calculate_new_beta()
        tick = util.get_tick(algo.session)

    while tick > 10 and tick <= 340:
        algo.update_returns()
        algo.calculate_new_beta()
        algo.evaluate_value()
        tick = util.get_tick(algo.session)


        
main()