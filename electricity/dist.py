import signal
import requests
import re
from time import sleep
import pandas as pd
import numpy as np

class ApiException(Exception):
    """Exception for API errors."""
    pass

def signal_handler(signum, frame):
    """Handle interrupt signals."""
    global shutdown
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Reset default signal handler
    shutdown = True

def get_temperature_forecast(session):
    """Fetch temperature forecast."""
    resp = session.get('http://localhost:9999/v1/news')
    if resp.ok:
        return resp.json()
    raise ApiException('Failed to fetch temperature forecast')

def calculate_expected_demand(temperature):
    """Calculate expected electricity demand based on temperature."""
    return 200 - 15 * temperature + 0.8 * temperature**2 - 0.01 * temperature**3

def get_parse_news(news):
    """"Parse the news"""
    for n in news:
        if "between" in n:
            temperatures = re.findall(r'\b\d+\b', n)
            temperatures = [int(temp) for temp in temperatures]
        
        return (temperatures[0]+temperatures[1])/2


def main():
    API_KEY = {'X-API-Key': 'Q8RYICSY'}
    shutdown = False
    session = requests.Session()
    session.headers.update(API_KEY)

    while not shutdown:
        try:
            temperature_forecast = get_temperature_forecast(session)
            parse_news = get_parse_news(temperature_forecast)

            expected_demand = calculate_expected_demand(parse_news)
            print("expected demand:" + expected_demand)
            
            
        except ApiException as e:
            print(f"API Error: {e}")
            break  # Exit loop on API error
        
        sleep(60)  # Wait for a minute before next cycle

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()
