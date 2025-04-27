import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# READINGS DATA FROM HOLDINGS.CSV
def load_holdings(file_path="holdings.csv"):
    holdings_df = pd.read_csv(file_path, dayfirst=True)
    holdings_df['Date'] = pd.to_datetime(holdings_df['Date'], dayfirst=True)
    return holdings_df

# Store the holdings into a dictionary for easy use
def process_holdings(holdings_df):
    holdings_dict = {}
    for i, row in holdings_df.iterrows():
        symbol = row['Symbol']
        if symbol not in holdings_dict:
            holdings_dict[symbol] = []

        entry = {
            'Date': row['Date'].strftime('%Y-%m-%d'),
            'Entry': row['Entry'],
            'Quantity': row['Quantity']
        }

        if entry not in holdings_dict[symbol]:
            holdings_dict[symbol].append(entry)
    return holdings_dict

# Fetch historical price data
def fetch_historical_data(holdings_dict, start_date, end_date):
    historical_data = {}
    for symbol, purchases in holdings_dict.items():
        total_quantity = sum(purchase['Quantity'] for purchase in purchases)
        total_cost = sum(purchase['Entry'] * purchase['Quantity'] for purchase in purchases)
        average_entry_price = total_cost / total_quantity

        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)

        if not df.empty:
            data = {date.strftime("%Y-%m-%d"): round(close_price, 2) for date, close_price in zip(df.index, df['Close'])}
            historical_data[symbol] = data
        else:
            print(f"No historical data found for {symbol}")
    return historical_data

# Compute daily PnL for each holding
def calculate_pnl(holdings_dict, historical_data, start_date, end_date):
    daily_rows = []
    current_date = start_date
    while current_date <= end_date:
        today_str = current_date.strftime("%Y-%m-%d")
        for symbol, purchases in holdings_dict.items():
            daily_qty = 0
            total_cost = 0
            for p in purchases:
                if today_str >= p["Date"]:  # p["Date"] is already a string
                    daily_qty += p["Quantity"]
                    total_cost += p["Entry"] * p["Quantity"]
            if daily_qty > 0:
                avg_price = total_cost / daily_qty
                close_price = historical_data.get(symbol, {}).get(today_str)
                if close_price is not None:
                    pnl = (close_price - avg_price) * daily_qty
                    daily_rows.append({
                        "Date": today_str,
                        "Symbol": symbol,
                        "Close Price": close_price,
                        "Avg Entry Price": round(avg_price, 2),
                        "Quantity": daily_qty,
                        "PnL": round(pnl, 2)
                    })
        current_date += timedelta(days=1)
    return daily_rows
