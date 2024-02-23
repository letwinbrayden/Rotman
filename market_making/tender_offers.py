import ritc
from time import sleep

# Replace with your actual API key
API_KEY = 'FPPGZ41T'

# Initialize RIT client
rit_client = ritc.RIT(x_api_key=API_KEY)

def fetch_current_price(ticker):
    """
    Fetch the current market price for a given ticker.
    """
    securities = rit_client.get_securities(ticker=ticker)
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

def handle_tender_offers():
    """
    Handles all active tender offers conservatively.
    """
    try:
        active_tenders = rit_client.get_tenders()
    except Exception as e:
        print(f"Error fetching tenders: {e}")
        return

    for tender in active_tenders:
        try:
            current_price = fetch_current_price(tender.ticker)
            if is_offer_profitable(tender, current_price):
                rit_client.post_tenders(tender.tender_id)
                print(f"Accepted offer on {tender.ticker}")
        except Exception as e:
            print(f"Error handling tender offer for {tender.ticker}: {e}")

def main():
    """
    Main loop to continuously check and handle tender offers.
    """
    while True:  # Modify as needed for your specific conditions
        handle_tender_offers()
       # sleep(2)  # Wait for X seconds before checking again to manage API rate limits

if __name__ == "__main__":
    main()
    security = securities[0]
    # Use bid for selling and ask for buying
    return (security.bid, security.ask)

def is_profitable_offer(tender: Tender, bid_price: float, ask_price: float) -> bool:
    """Determine if the tender offer is profitable."""
    profit_margin_threshold = 0.02  # Set a threshold for minimum profit margin (e.g., 2%)
    if tender.action == 'BUY':
        # The institution wants to sell to us: Check if we can buy below the market price
        return tender.price < ask_price * (1 - profit_margin_threshold)
    elif tender.action == 'SELL':
        # The institution wants to buy from us: Check if we can sell above the market price
        return tender.price > bid_price * (1 + profit_margin_threshold)
    return False

def handle_tender_offers():
    """Handle tender offers based on the strategy."""
    tenders = rit_client.get_tenders()
    for tender in tenders:
        bid_price, ask_price = fetch_current_market_price(tender.ticker)
        if is_profitable_offer(tender, bid_price, ask_price):
            # Accept the tender offer
            try:
                rit_client.post_tenders(id=tender.tender_id)
                print(f"Accepted tender offer for {tender.ticker}")
            except Exception as e:
                print(f"Error accepting tender offer: {e}")
        else:
            print(f"Tender offer for {tender.ticker} not profitable, skipped")

# Main loop
while True:
    handle_tender_offers()
    #time.sleep(30)  # Wait for some time before checking again
