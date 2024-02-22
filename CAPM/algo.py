import util
import statsmodels.api as sm
import numpy as np
import pandas as pd
from time import sleep
import re

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
        self.future_tick = -1
        self.future_market_value = -1

    def start_session(self):
        print("Session Not Active.")
        while True:
            tick = util.get_tick(self.session)
            if tick >= 1:
                info = util.get_news(self.session)[-1]
                info = info['body']
                self.tickers['ALPHA']['BETA'], self.tickers['GAMMA']['BETA'], self.tickers['THETA']['BETA'] = self.extract_numbers(info)[2:]
                self.news = info
                print("Session Active.")
                return
    
    def extract_numbers(self, input_string):
        pattern = r'-?\d+\.?\d*'
        return [float(match) if '.' in match else int(match) for match in re.findall(pattern, input_string)]

    def update_news(self):
        news = util.get_news(self.session)
        if news != self.news:
            self.news = news
            info = self.extract_numbers(self.news[0]['body'])
            self.future_tick = info[0]
            self.future_market_value = info[1]
    
    def update_returns(self):
        prices = util.get_prices(self.session)
        if self.index_last_price == -1:
            self.index_returns.append(0)
        else:
            self.index_returns.append((prices["RITM"] - self.index_last_price) / self.index_last_price)
        self.index_last_price = prices["RITM"]
        if len(self.index_returns) >= 100:
            self.index_returns.pop(0)

        for ticker in self.tickers:
            if self.last_prices[ticker] == -1:
                self.returns[ticker].append(0)
            else:
                self.returns[ticker].append((prices[ticker] - self.last_prices[ticker]) / self.last_prices[ticker])
            self.last_prices[ticker] = prices[ticker]
            if len(self.returns[ticker]) >= 100:
                self.returns[ticker].pop(0)
        return
        
    def place_order(self, ticker, qty, trade_decision):
        orders_placed = 0
        while trade_decision == 'BUY' and orders_placed < 10:
            util.place_mkt_buy_order(self.session, ticker, qty)
            orders_placed += 1
            sleep(0.1)
        while trade_decision == 'SELL' and orders_placed < 10:
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
        return (self.tickers[ticker]["BETA"] * market_return)
        
    def clear_position(self, stock = None):
        print('clearing pos')
        for ticker in self.tickers:
            while util.get_position(self.session, ticker) > 0:
                util.place_mkt_sell_order(self.session, ticker, 10000)
                sleep(0.1)
            while util.get_position(self.session, ticker) < 0:
                util.place_mkt_buy_order(self.session, ticker, 10000)
                sleep(0.1)

    def clear_neg_position(self, stock = None):
        if stock == None:
            for ticker in self.tickers:
                position = util.get_position(self.session, ticker)
                while position < 0:
                    util.place_mkt_buy_order(self.session, ticker, 10000)
                    position = util.get_position(self.session, ticker)
        else:
            ticker = stock
            position = util.get_position(self.session, ticker)
            while position < 0:
                util.place_mkt_buy_order(self.session, ticker, 10000)
                position = util.get_position(self.session, ticker)
    
    def clear_pos_position(self, stock = None):
        if stock == None:
            for ticker in self.tickers:
                position = util.get_position(self.session, ticker)
                while position > 0:
                    util.place_mkt_sell_order(self.session, ticker, 10000)
                    position = util.get_position(self.session, ticker)
        else:
            ticker = stock
            position = util.get_position(self.session, ticker)
            while position > 0:
                util.place_mkt_sell_order(self.session, ticker, 10000)
                position = util.get_position(self.session, ticker)
    
    def calculate_beta(self):
        for ticker in self.tickers:
            covariance = np.cov(self.returns[ticker], self.index_returns)[0, 1]
            market_variance = np.var(self.index_returns)
            self.tickers[ticker]["BETA"] = covariance / market_variance
            print(self.tickers[ticker]["BETA"])

def main():
    algo = Algo()
    algo.start_session()
    tick = util.get_tick(algo.session)
    while tick >= 1 and tick <= 10:
        algo.update_returns()
        tick = util.get_tick(algo.session)
        sleep(0.5)

    big_tick = 10
    while tick > 10 and tick <= 600:
        algo.update_returns()
        algo.update_news()
        if algo.future_tick != big_tick:
            big_tick = algo.future_tick
            if algo.future_market_value > util.get_prices(algo.session)['RITM']:
                algo.clear_neg_position()
                for ticker in ["ALPHA"]:
                    algo.place_order(ticker, 10000, "BUY")
            elif algo.future_market_value < util.get_prices(algo.session)['RITM']:
                algo.clear_pos_position()
                for ticker in ["ALPHA"]:
                    algo.place_order(ticker, 10000, "SELL")
        if sum(util.unrealized_pft(algo.session)) >= 250000:
            algo.clear_position()
            algo.clear_position() 
        print(algo.future_tick, tick)
        algo.calculate_beta()
        tick = util.get_tick(algo.session)
        sleep(0.5) 
main()