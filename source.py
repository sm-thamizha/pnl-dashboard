import os
import requests
import pandas as pd
from datetime import datetime
import webbrowser
from fyers_apiv3 import fyersModel
from datetime import timedelta

client_id = 'DP24B3W02G-100'
secret_key = '2HYDZFCY55'
redirect_uri = 'https://www.google.com'
access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0FMNmkxTVdQMUo4cFFYbDdzeExfLVd6enVHZEhjWHRVSUoydjAyc0JiT29lMHczazVqUV92Zlo1eTFSV1YtWV9idkpmdEtLVEVRR0N3SFhJLUZQWEd1UUpqLU02ZmowWkdMbHVZc2lTZTFGQ3FKQT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiI2ZTA3ZDM5MDIyNWMwMjU3NDA2ZDc2YzMzODVhNzJjMjc2OGVmODQ1OWVmNGRkZDlhYTk1Y2ZkYyIsImlzRGRwaUVuYWJsZWQiOiJZIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWVMzNDM4NyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0OTM2MjAwLCJpYXQiOjE3NDQ4NzkyNjYsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDg3OTI2Niwic3ViIjoiYWNjZXNzX3Rva2VuIn0.D_ZvH07cmhyZKJ0e5XkvyWsKT3mB63GtSZzUYG0talQ'

fyers = fyersModel.FyersModel(token=access_token, is_async=False, client_id=client_id, log_path="")

start_date = None
pnl_file = "/opt/render/project/src/holdings_pnl_tracker.csv"
holdings_df = pd.read_csv("/opt/render/project/src/holdings.csv", dayfirst=True)
holdings_df['Date'] = pd.to_datetime(holdings_df['Date'], dayfirst=True)

holdings_dict = holdings_df.groupby('Symbol').apply(
    lambda x: x[['Date', 'Entry', 'Quantity']].apply(lambda row: {
        'Date': row['Date'].strftime('%Y-%m-%d'),
        'Entry': row['Entry'],
        'Quantity': row['Quantity']
    }, axis=1).to_list()
).to_dict()

if os.path.exists(pnl_file):
    pnl_df = pd.read_csv(pnl_file)
    pnl_df['Date'] = pd.to_datetime(pnl_df['Date'], format='%Y-%m-%d')
    pnl_df.sort_values(by='Date', inplace=True)
    last_date = pnl_df['Date'].max()
    start_date = last_date + timedelta(days=1)
else:
    start_date = min([purchase["Date"] for purchases in holdings_dict.values() for purchase in purchases])
#print(holdings_dict)

end_date = datetime.today()

historical_data = {}

for symbol, purchases in holdings_dict.items():
    total_quantity = sum(purchase['Quantity'] for purchase in purchases)
    total_cost = sum(purchase['Entry'] * purchase['Quantity'] for purchase in purchases)
    average_entry_price = total_cost / total_quantity
    #print(f"📥 Fetching historical data for {symbol}")
    res = fyers.history({
        "symbol": symbol,
        "resolution": "D",
        "date_format": "1",
        "range_from": min([p["Date"] for p in purchases]),
        "range_to": end_date.strftime("%Y-%m-%d"),
        "cont_flag": "1"
    })
    #print(f"API response for {symbol}: {res}")
    candles = res.get("candles", [])
    if candles:
        data = {}
        for candle in candles:
            date = datetime.fromtimestamp(candle[0]).strftime("%Y-%m-%d")
            close_price = candle[4]
            data[date] = close_price
        historical_data[symbol] = data
    else:
        print(f"No historical data found for {symbol}")

daily_rows = []
current_date = start_date

while current_date <= end_date:
    today_str = current_date.strftime("%Y-%m-%d")
    for symbol, purchases in holdings_dict.items():
        daily_qty = 0
        total_cost = 0
        for p in purchases:
            if today_str >= p["Date"]:
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

if daily_rows:
    df = pd.DataFrame(daily_rows)
    df.sort_values(by=["Date", "Symbol"], inplace=True)
    print(df)
    df.to_csv("holdings_pnl_tracker.csv", index=False)
