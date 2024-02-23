from ritc import RIT, Tender, Security
import time

# Initialize RIT Client
API_KEY = "your_api_key_here"  # Replace with your API key
rit_client = RIT(x_api_key=API_KEY)

def fetch_current_market_price(ticker: str) -> float:
    """Fetch the current market price for a given ticker."""
    securities = rit_client.get_securities(ticker=ticker)
    security = securities[0]
    return (security.bid + security.ask) / 2  # Average of bid and ask price

def is_profitable_offer(tender: Tender, current_market_price: float) -> bool:
    """Determine if the tender offer is profitable."""
    profit_margin_threshold = 0.02  # Set a threshold for minimum profit margin (e.g., 2%)
    if tender.action == 'BUY':
        # If buying, the offer price should be significantly lower than the market price
        return current_market_price > tender.price * (1 + profit_margin_threshold)
    elif tender.action == 'SELL':
        # If selling, the offer price should be significantly higher than the market price
        return tender.price > current_market_price * (1 + profit_margin_threshold)
    return False

def handle_tender_offers():
    """Handle tender offers based on the strategy."""
    tenders = rit_client.get_tenders()
    for tender in tenders:
        current_price = fetch_current_market_price(tender.ticker)
        if is_profitable_offer(tender, current_price):
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
    time.sleep(30)  # Wait for some time before checking again
