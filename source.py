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
pnl_file = "holdings_pnl_tracker.csv"
holdings_df = pd.read_csv("holdings.csv", dayfirst=True)
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
    
    
import plotly.express as px
import plotly.graph_objects as go

holdings_file = "holdings.csv"
pnl_file = "holdings_pnl_tracker.csv"

holdings_df = pd.read_csv(holdings_file)
df = pd.read_csv(pnl_file)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date

df_total = df.groupby('Date')['PnL'].sum().reset_index()

df_total['Month'] = pd.to_datetime(df_total['Date']).dt.to_period('M').dt.to_timestamp()
first_trading_days = df_total.groupby('Month').first().reset_index()
tick_dates = first_trading_days['Date'].tolist()

df_total['Line Color'] = df_total['PnL'].apply(lambda x: 'green' if x >= 0 else 'red')
df_total['Marker Color'] = df_total['PnL'].apply(lambda x: 'green' if x >= 0 else 'red')

fig = go.Figure()

fig.update_xaxes(
    tickmode='array',
    tickvals=tick_dates,
    tickformat="%b %Y"
)

for i in range(1, len(df_total)):
    x0 = pd.to_datetime(df_total['Date'][i-1])
    x1 = pd.to_datetime(df_total['Date'][i])
    y0 = df_total['PnL'][i-1]
    y1 = df_total['PnL'][i]

    if (y0 < 0 and y1 >= 0) or (y0 >= 0 and y1 < 0):
        # Find the zero crossing point via linear interpolation
        crossing_ratio = abs(y0) / (abs(y0) + abs(y1))
        crossing_time = x0 + (x1 - x0) * crossing_ratio

        # Draw first segment (x0 to crossing point)
        fig.add_scatter(
            x=[x0, crossing_time],
            y=[y0, 0],
            mode='lines',
            line=dict(color='red' if y0 < 0 else 'green', width=3),
            showlegend=False,
            hoverinfo='skip'
        )

        # Draw second segment (crossing point to x1)
        fig.add_scatter(
            x=[crossing_time, x1],
            y=[0, y1],
            mode='lines',
            line=dict(color='green' if y1 >= 0 else 'red', width=3),
            showlegend=False,
            hoverinfo='skip'
        )
    else:
        # No crossing — same color throughout
        line_color = 'green' if y1 >= 0 else 'red'
        fig.add_scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode='lines',
            line=dict(color=line_color, width=3),
            showlegend=False,
            hoverinfo='skip'
        )

fig.add_scatter(
    x=df_total['Date'],
    y=df_total['PnL'],
    mode='none',
    hovertemplate="Date: %{x|%d-%m-%Y}<br>Total PnL: %{y}<extra></extra>",
    showlegend=False
)

fig.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    title="Portfolio PnL Over Time",
    template='plotly_dark'
)

fig.show()
html_graph = fig.to_html(include_plotlyjs='cdn', full_html=False)

# This part needs to be corrected to aggregate correctly based on Ticker and update the invested and quantity.
portfolio_data = {}

for _, row in holdings_df.iterrows():
    ticker = row['Symbol']
    quantity = row['Quantity']
    price = row['Entry']  # Assuming you have the 'Price' column in holdings.csv

    # Aggregate total quantity and total invested for each ticker
    if ticker not in portfolio_data:
        portfolio_data[ticker] = {
            'Total Qty': 0,
            'Total Invested': 0
        }

    portfolio_data[ticker]['Total Qty'] += quantity
    # Aggregate total quantity and total invested for each ticker
    portfolio_data[ticker]['Total Invested'] += round(quantity * price, 2)  # Round to 2 decimal places


portfolio_table = "<table border='1' style='width:100%; margin-top: 30px; text-align: center; border-collapse: collapse;'>"
portfolio_table += "<tr><th>Ticker</th><th>Quantity</th><th>Invested</th><th>Current PnL</th><th>PnL %</th></tr>"

# Calculate total invested
total_invested = sum([data['Total Invested'] for data in portfolio_data.values()])

# Iterate through portfolio dictionary and extract the current PnL from the pnl file
for ticker, data in portfolio_data.items():
    # Extract latest PnL for the ticker
    latest_pnl = df[df['Symbol'] == ticker]['PnL'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
    # Calculate PnL percentage for the stock
    pnl_percentage = (latest_pnl / data['Total Invested']) * 100 if data['Total Invested'] != 0 else 0
    
    portfolio_table += f"<tr><td>{ticker}</td><td>{data['Total Qty']}</td><td>{data['Total Invested']}</td><td>{latest_pnl}</td><td>{pnl_percentage:.2f}%</td></tr>"

portfolio_table += "</table>"

# Build full HTML page with graph and portfolio table
html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>📈 My Portfolio Tracker</title>
    <style>
        body {{
            background-color: #121212;
            color: white;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            margin-top: 0;
        }}
        .info {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .plot {{
            width: 100%;
            max-width: 1000px;
            margin: auto;
        }}
        table {{
            width: 100%;
            margin-top: 30px;
            border-collapse: collapse;
            text-align: center;
            table-layout: auto;
        }}
        th, td {{
            padding: 8px;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #444;
        }}
    </style>
</head>
<body>
    <h1>📊 Portfolio Dashboard</h1>
    <div class="info">
        <p>Owner: <strong>SM Thamizha</strong></p>
        <p>Last Updated: {datetime.today().strftime('%d-%m-%Y')}</p>
    </div>
    <div class="plot">
        {html_graph}
    </div>

    <div class="portfolio">
        <h2 style="text-align: center;">Portfolio Overview</h2>
        {portfolio_table}
    </div>
</body>
</html>
"""

# Write the full HTML to index.html
with open("index.html", "w") as f:
    f.write(html_template)


import subprocess
key = os.getenv("SSH_PRIVATE_KEY").replace("#", "\n")
print(key)
subprocess.run(["eval", "$(ssh-agent -s)"], shell=True)
process = subprocess.Popen(["ssh-add", "-"], stdin=subprocess.PIPE)
process.communicate(input=key.encode())
subprocess.run(["ssh-add","-l"], shell=True)

# SSH URL for your repository
repo_url = "git@github.com:sm-thamizha/pnl-dashboard-trial.git"

# Ensure remote URL is set correctly for 'origin' using SSH
try:
    subprocess.run(['git', 'remote', 'get-url', 'origin'], check=True)
    print("Remote 'origin' exists.")
except subprocess.CalledProcessError:
    print("Remote 'origin' does not exist. Adding 'origin'.")
    subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)

# Verify remote URL configuration
subprocess.run(['git', 'remote', '-v'], check=True)

# Checkout the 'main' branch (if not on 'main' already)
subprocess.run(['git', 'checkout', '-B', 'main'], check=True)

# Set user identity for commits (optional, but recommended even with SSH)
subprocess.run(['git', 'config', 'user.name', 'SM Thamizha'], check=True)
subprocess.run(['git', 'config', 'user.email', 'psakthimurugan1@gmail.com'], check=True)

# Add index.html to staging (ensure the file is tracked)
subprocess.run(['git', 'add', 'index.html'], check=True)

# Check status to ensure the file is added
subprocess.run(['git', 'status'], check=True)

# Commit the changes with a meaningful message
subprocess.run(['git', 'commit', '-m', 'Update portfolio dashboard with the latest graph'], check=True)

# Push the changes to the 'main' branch using SSH
subprocess.run(['git', 'push', 'origin', 'main'], check=True)

print("Changes successfully pushed to GitHub using SSH!")
