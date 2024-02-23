import pandas as pd
import ritc
from openpyxl import Workbook
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

def fetch_historical_data(ticker):
    """
    Fetch the historical data for a given ticker.
    """
    history = rit_client.get_securities_history(ticker=ticker)
    return pd.DataFrame(history)

def calculate_volatility(df):
    """
    Calculate the volatility based on historical data.
    """
    # Assuming 'close' price is available for volatility calculation
    return df['close'].pct_change().std()

def update_excel_sheet(writer, data, sheet_name):
    """
    Update the Excel sheet with new data.
    """
    data.to_excel(writer, sheet_name=sheet_name, index=False)

def main():
    tickers = ['RIT_U', 'RIT_C', 'CAD', 'USD']  # Add all required tickers
    volatility_data = []
    price_data = []

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter('stock_data.xlsx', engine='xlsxwriter')

    for ticker in tickers:
        current_price = fetch_current_price(ticker)
        historical_data = fetch_historical_data(ticker)
        volatility = calculate_volatility(historical_data)

        price_data.append({'Ticker': ticker, 'Current Price': current_price})
        volatility_data.append({'Ticker': ticker, 'Volatility': volatility})

    price_df = pd.DataFrame(price_data)
    volatility_df = pd.DataFrame(volatility_data)

    update_excel_sheet(writer, price_df, 'Current Prices')
    update_excel_sheet(writer, volatility_df, 'Volatility')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

if __name__ == "__main__":
    main()
