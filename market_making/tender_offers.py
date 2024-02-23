import ritc
from time import sleep

# Replace with your actual API key
API_KEY = 'YOUR_API_KEY'

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
                result = rit_client.post_tenders(tender.tender_id)
                print(f"Accepted offer on {tender.ticker}: {result}")
            else:
                print(f"Offer not profitable for {tender.ticker}")
        except Exception as e:
            print(f"Error handling tender offer for {tender.ticker}: {e}")

def main():
    """
    Main loop to continuously check and handle tender offers.
    """
    while True:  # Modify as needed for your specific conditions
        handle_tender_offers()
        sleep(60)  # Wait for 60 seconds before checking again to manage API rate limits

if __name__ == "__main__":
    main()