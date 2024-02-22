import signal
import requests
from time import sleep
import pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.DataFrame(columns=['ticker', 'last', 'time_period'])
time = 0 

class ApiException(Exception):
    """Exception for API errors."""
    pass

def signal_handler(signum, frame):
    """Handle interrupt signals to gracefully shut down."""
    global shutdown
    shutdown = True

def fetch_new_data_point(session):
    """Fetch new data points from the API."""
    global time
    resp = session.get('http://localhost:9999/v1/securities') 
    if resp.ok:
        new_data = []
        time += 1  
        for j in resp.json():
            new_data.append({'ticker': j['ticker'], 'last': j['last'], 'time_period': time})
        return new_data
    else:
        raise ApiException('Failed to fetch securities')

def update_analysis():
    """Perform linear regression analysis and print useful output, including overall and recent trend strength, and basic safety assessment."""
    for ticker in ['RITC', 'COMP']:
        df_ticker = df[df['ticker'] == ticker]
        if not df_ticker.empty:  
            X = df_ticker[['time_period']].values.reshape(-1, 1)
            y = df_ticker['last']
            
            reg = LinearRegression().fit(X, y)
            
            slope = reg.coef_[0]
            direction = "upward" if slope > 0 else "downward"
            overall_strength = abs(slope)
            overall_trend_strength = "strong" if overall_strength > 0.5 else "medium" if overall_strength > 0.1 else "weak"
            
            if len(X) > 10:
                X_recent = X[-10:]
                y_recent = y.iloc[-10:]
                reg_recent = LinearRegression().fit(X_recent, y_recent)
                recent_slope = reg_recent.coef_[0]
                recent_trend_strength = "recently stronger" if abs(recent_slope) > abs(slope) else "recently weaker" if abs(recent_slope) < abs(slope) else "consistent"
            else:
                recent_slope = "N/A"
                recent_trend_strength = "not enough data for recent trend analysis"
            
            volatility = y.std()
            safety = "safer" if slope/volatility > 0.1 else "risky"
            
            recent_change = y.iloc[-1] - y.iloc[-2] if len(y) > 1 else "N/A"
            average_price = y.mean()
            
            print(f"Ticker: {ticker}")
            print(f"Overall Trend: {direction} ({overall_trend_strength})")
            print(f"Recent Trend Analysis (last 10 periods): {recent_trend_strength}, Recent Slope: {recent_slope}")
            print(f"Safety: {safety} (based on slope to volatility ratio)")
            print(f"Recent Price Change: {recent_change}")
            print(f"Volatility: {volatility}")
            print(f"Average Price: {average_price}\n")

            
def main():
    API_KEY = {'X-API-Key': 'Q8RYICSY'}  # Ensure this is your correct API key
    global shutdown
    shutdown = False
    session = requests.Session()
    session.headers.update(API_KEY)

    while not shutdown:
        try:
            new_data_points = fetch_new_data_point(session)
            global df
            df = pd.concat([df, pd.DataFrame(new_data_points)], ignore_index=True)
            update_analysis()  
        except ApiException as e:
            print(f"API Error: {e}")
            break
        sleep(1)  

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    main()