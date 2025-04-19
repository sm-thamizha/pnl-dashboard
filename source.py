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
portfolio_table += "<tr><th>Ticker</th><th>Quantity</th><th>Invested</th><th>PnL (₹)</th><th>PnL (%)</th></tr>"

# Calculate total invested
total_invested = sum([data['Total Invested'] for data in portfolio_data.values()])

current_value = 0
for ticker, data in portfolio_data.items():
    latest_price = df[df['Symbol'] == ticker]['Close Price'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
    current_value += latest_price * data['Total Qty']

total_pnl = current_value - total_invested
pnl_percent = (total_pnl / total_invested) * 100 if total_invested != 0 else 0

# Iterate through portfolio dictionary and extract the current PnL from the pnl file
for ticker, data in portfolio_data.items():
    # Extract latest PnL for the ticker
    latest_pnl = df[df['Symbol'] == ticker]['PnL'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
    # Calculate PnL percentage for the stock
    pnl_percentage = (latest_pnl / data['Total Invested']) * 100 if data['Total Invested'] != 0 else 0
    
    portfolio_table += f"<tr><td>{ticker}</td><td>{data['Total Qty']}</td><td>{data['Total Invested']}</td><td>{latest_pnl}</td><td>{pnl_percentage:.2f}%</td></tr>"

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>📈 Portfolio Dashboard</title>

  <!-- Google Fonts for custom font styles -->
  <link href="https://fonts.googleapis.com/css2?family=Lobster&family=EB+Garamond&display=swap" rel="stylesheet">

  <!-- Plotly.js for interactive charts -->
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

  <!-- CSS Styling -->
  <style>
    /* General body styles */
    body {{
      background-color: #fff8e1; /* Light yellow background */
      color: #3e2723;             /* Dark brown text */
      font-family: 'EB Garamond', serif;
      padding: 2rem;
    }}

    /* Header section layout */
    .header {{
      display: flex;
      justify-content: space-between; /* Title on left, info on right */
      align-items: flex-start;
      margin-bottom: 2rem;
    }}

    /* Dashboard title style */
    h1 {{
      font-family: 'Lobster', cursive;
      font-size: 3rem;
      color: #ff6f00;
      text-shadow: 2px 2px #00000044;
      margin: 0;
    }}

    /* Owner and date info */
    .info {{
      text-align: right;
      font-size: 1rem;
      color: #6d4c41;
      line-height: 1.2;
      font-family: 'EB Garamond', serif;
    }}

    /* Summary boxes container */
    .summary {{
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 2rem;
      margin-bottom: 2rem;
    }}

    /* Individual summary box styling */
    .summary-item {{
      font-size: 1.25rem;
      padding: 1rem;
      background-color: #fff3cd;  /* Light yellow-orange background */
      border: 2px solid #ffcf40;  /* Yellow border */
      border-radius: 10px;
      min-width: 250px;
      text-align: center;
      font-weight: bold;
      color: #5d4037;
    }}

    /* Main content layout: Chart + Table side-by-side */
    .content {{
      display: flex;
      gap: 2rem;
    }}

    /* Chart container */
    #pnlChart {{
      flex: 1.2;
      height: 500px;
    }}

    /* Table container (with scroll if needed) */
    .table-container {{
      flex: 1;
      overflow-x: auto;
    }}

    /* Table styling */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
      font-size: 0.95rem;
    }}

    /* Table cell styles */
    th, td {{
      padding: 0.75rem;
      text-align: center;
      border: 1px solid #bcaaa4;
      white-space: nowrap;
    }}

    /* Table header styling */
    th {{
      background-color: #ffe082;  /* Soft yellow */
      color: #4e2600;
      font-weight: bold;
    }}

    /* Zebra stripe effect for table rows */
    tbody tr:nth-child(even) {{
      background-color: #fffde7;
    }}

    /* Hover effect for rows */
    tbody tr:hover {{
      background-color: #fce4ec;
    }}

    /* Text color helpers for PnL positive/negative */
    .text-green {{
      color: #2e7d32;
    }}

    .text-red {{
      color: #c62828;
    }}
  </style>
</head>

<body>

  <!-- Dashboard Header Section -->
  <div class="header">
    <h1>📊 Portfolio Dashboard</h1>
    <div class="info">
      <div><strong>Owner:</strong> SM Thamizha</div>
      <div><strong>Last Updated:</strong> {datetime.today().strftime('%d-%m-%Y')}</div>
    </div>
  </div>

  <!-- Summary Boxes -->
  <div class="summary">
    <div class="summary-item">
      💰 <strong>Total Invested:</strong> ₹{total_invested:,.2f}
    </div>
    <div class="summary-item">
      📈 <strong>Current Value:</strong> ₹{current_value:,.2f}
    </div>
    <div class="summary-item">
      📊 <strong>Portfolio PnL:</strong> ₹{total_pnl:,.2f} ({pnl_percent:.2f}%)
    </div>
  </div>

  <!-- Main Chart + Table Layout -->
  <div class="content">

    <!-- Portfolio PnL Line Chart -->
	<div class="plot">
		{html_graph}
	</div>

  <!-- Holdings Table -->
  <div class="table-container">
    <h3>📋 Holdings Overview</h3>
    <table>
      <tbody id="holdingsTable">
        <!-- Your generated portfolio table rows will be inserted here -->
        {portfolio_table}
      </tbody>
    </table>
  </div>

</body>
</html>"""

# Write the full HTML to index.html
with open("index.html", "w") as f:
    f.write(html_template)
