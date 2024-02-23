import requests
import sys

"""

python balance_positions.py balance

"""


BASE_URL = "http://localhost:9999/v1"
API_KEY = "your_api_key_here"  # Replace with your actual API key
HEADERS = {"X-API-Key": API_KEY}

def send_request(method, endpoint, params=None, data=None):
    """Send an HTTP request to the RIT Client API."""
    url = f"{BASE_URL}/{endpoint}"
    try:
        response = requests.request(method, url, headers=HEADERS, params=params, json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as err:
        print(f"Error occurred: {err}")
        sys.exit(1)

def get_positions():
    """Get all current positions."""
    return send_request("GET", "securities")

def place_order(ticker, action, quantity):
    """Place a market order to balance a position."""
    data = {"ticker": ticker, "type": "MARKET", "quantity": quantity, "action": action}
    return send_request("POST", "orders", data=data)

def balance_positions():
    """Balance all positions to zero."""
    positions = get_positions()
    for pos in positions:
        if pos['position'] != 0:
            action = "SELL" if pos['position'] > 0 else "BUY"
            quantity = abs(pos['position'])
            print(f"Balancing {pos['ticker']}: {action}ing {quantity} shares")
            place_order(pos['ticker'], action, quantity)
    print("All positions balanced.")

def main():
    if len(sys.argv) == 2 and sys.argv[1].lower() == 'balance':
        balance_positions()
    else:
        print("Usage: python balance_positions.py balance")

if __name__ == "__main__":
    main()
