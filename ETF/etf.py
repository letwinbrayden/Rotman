import util
from rit import *
from time import sleep

class ETFALGO:
    def __init__(self):
        self.session = util.open_session()
        self.tickers = {"RITC", "COMP"}
        self.ticker_bids = {"RITC": [], "COMP": []}
        self.ticker_asks = {"RITC": [], "COMP": []}

    
    def start_session(self):
        print("Session Not Active.")
        while True:
            tick = util.get_tick(self.session)
            if tick >= 1:
                print("Session Active.")
                return tick
    
    def handle_tenders(self):
        tenders = util.get_tenders()
        for tender in tenders:

            
            if tender["caption"].startswith("An institution would like to"):
                print("private offer found at tick: ", tender["tick"])



            # # Implement your decision logic here. Example:
            # # Check if the tender price is favorable compared to the current market price
            # market_price = rit.get_securities(ticker=tender['ticker'])[0].last_price
            # if tender['price'] >= market_price * 1.05:  # Example criterion
            #     try:
            #         rit.post_tenders(tender['tender_id'], price=tender['price'])
            #         print(f"Accepted tender {tender['tender_id']} at price {tender['price']}")
            #     except Exception as e:
            #         print(f"Error accepting tender {tender['tender_id']}: {e}")
            # else:
            #     try:
            #         rit.delete_tenders(tender['tender_id'])
            #         print(f"Declined tender {tender['tender_id']}")
            #     except Exception as e:
            #         print(f"Error declining tender {tender['tender_id']}: {e}")


    # categorize the offers into 3 types: private, comp, winner takes all
        # observe the offer strings, see if there's a pattern to identify (simple if statements)
                    
                # private
                    # "An institution would like to [SELL/BUY]"
                    
                # comp
                    
                # winner takes all

        
    def update_pricing(self, ticker):
        bids, highest_bid = util.get_bid_orders(self.session, ticker)
        asks, lowest_ask = util.get_ask_orders(self.session, ticker)
        self.ticker_bids[ticker].append(highest_bid)
        self.ticker_asks[ticker].append(lowest_ask)

def main():
    algo = ETFALGO()
    tick = algo.start_session()
    while tick >= 1 and tick <= 600:
        print("TICK: {}".format(tick))
        print("-" * 11)
        for ticker in algo.tickers:
            algo.update_pricing(ticker)
            print("Ask: $ {}".format(algo.ticker_asks[ticker]))
            print("Bid: $ {}".format(algo.ticker_bids[ticker]))
            print('\n' + "Percent Change (5 ticks): {}".format())
            print('\n' + "Percent Change (10 ticks): {}".format())
            print('\n' + "Percent Change (20 ticks): {}".format())
        sleep(1)
        tick = util.get_tick(algo.session)
        
        
        

if __name__ == "__main__":
    main()