import requests
import sys
import json

"""

python rit_script.py buy HAWK LIMIT 100 14.21

python rit_script.py cancel_all

python rit_script.py buy HAWK MARKET 100

python rit_script.py sell HAWK MARKET 50

"""

# Set the base URL and the API key for authentication
BASE_URL = "http://localhost:9999/v1"
API_KEY = "your_api_key_here"  # Replace with your actual API key

# Headers for the HTTP requests
HEADERS = {"X-API-Key": API_KEY}

def list_securities():
    """List all available securities."""
    response = send_request("GET", "securities")
    for security in response:
        print(f"{security['ticker']}: {security['description']}")


def send_request(method, endpoint, params=None, data=None):
    """Send an HTTP request to the RIT Client API."""
    url = f"{BASE_URL}/{endpoint}"
    if method == 'GET':
        response = requests.get(url, headers=HEADERS, params=params)
    elif method == 'POST':
        response = requests.post(url, headers=HEADERS, json=data)
    elif method == 'DELETE':
        response = requests.delete(url, headers=HEADERS, params=params)
    else:
        raise ValueError("Invalid HTTP method")

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.json())
        sys.exit(1)

def place_order(ticker, order_type, quantity, action, price=None):
    """Place an order."""
    data = {
        "ticker": ticker,
        "type": order_type.upper(),
        "quantity": quantity,
        "action": action.upper()
    }
    if price:
        data["price"] = price

    return send_request("POST", "orders", data=data)

def cancel_all_orders():
    """Cancel all open orders."""
    return send_request("POST", "commands/cancel")

def main():
    if len(sys.argv) < 2:
        print("Usage: python rit_script.py [command] [args...]")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == "buy" or command == "sell":
        if len(sys.argv) < 5:
            print(f"Usage: python rit_script.py {command} [ticker] [type] [quantity] [price (optional)]")
            sys.exit(1)

        ticker = sys.argv[2]
        order_type = sys.argv[3]
        quantity = int(sys.argv[4])
        price = float(sys.argv[5]) if len(sys.argv) > 5 else None

        response = place_order(ticker, order_type, quantity, command, price)
        print(json.dumps(response, indent=2))
    elif command == "cancel_all":
        response = cancel_all_orders()
        print(json.dumps(response, indent=2))

    elif command == "list_securities":
        list_securities()
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
