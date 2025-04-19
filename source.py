import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

holdings_df = pd.read_csv("holdings.csv", dayfirst=True)
holdings_df['Date'] = pd.to_datetime(holdings_df['Date'], dayfirst=True)

holdings_dict = {}

for _, row in holdings_df.iterrows():
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

# Display the resulting holdings_dict
'''for symbol, entries in holdings_dict.items():
    print(f"Symbol: {symbol}")
    
    for entry in entries:
        print(f"  Date: {entry['Date']}, Entry: {entry['Entry']}, Quantity: {entry['Quantity']}")
    print("\n")'''

start_date = min([datetime.strptime(purchase["Date"], "%Y-%m-%d")
                      for purchases in holdings_dict.values()
                      for purchase in purchases])

end_date = datetime.today()

historical_data = {}

for symbol, purchases in holdings_dict.items():
    total_quantity = sum(purchase['Quantity'] for purchase in purchases)
    total_cost = sum(purchase['Entry'] * purchase['Quantity'] for purchase in purchases)
    average_entry_price = total_cost / total_quantity
    
    # Fetch historical data using yfinance
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date)
    
    # Check if data is available
    if not df.empty:
	    data = {date.strftime("%Y-%m-%d"): round(close_price, 2) for date, close_price in zip(df.index, df['Close'])}
	    #print(data)
	    historical_data[symbol] = data
	    #print(historical_data[symbol])
    else:
        print(f"No historical data found for {symbol}")

#Optionally print out the historical data
'''for symbol, data in historical_data.items():
    for date, close_price in data.items():
        print(f"Symbol: {symbol}, Date: {date}, Close: {close_price}")'''

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
    yaxis=dict(
        tickformat=".2~s"  # Use SI prefix (k, M, etc.) and round to 2 decimals
    ),
    title="Portfolio PnL",
    template='ggplot2',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    font=dict(
        family="Silkscreen, sans-serif",
        size=12,
        color="#3e2723"
    )
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
portfolio_table += "<tr><th>Ticker</th><th>Quantity</th><th>Invested</th><th>PnL <span>(₹)</span></th><th>PnL <span>(%)</span></th></tr>"

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

if total_pnl > 0:
    pnl_class = "text-green"
else:
    pnl_class = "text-red"

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📈 Portfolio Dashboard</title>

  <!-- Google Fonts for custom font styles -->
  <link href="https://fonts.googleapis.com/css2?family=Bungee+Spice&family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">

  <!-- Plotly.js for interactive charts -->
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

  <!-- CSS Styling -->
  <style>
    /* General body styles */
    body {{
      background-color: #fff8e1; /* Light yellow background */
      color: #3e2723;             /* Dark brown text */
      font-family: 'Silkscreen', sans-serif;
      padding: 1rem 2rem 2rem 2rem;
    }}

    /* Header section layout */
    .header {{
      display: flex;
      justify-content: space-between;
      flex-direction: column; 
      align-items: center;
      width: 100%;
      position: relative;
    }}

    /* Dashboard title style */
    h1 {{
      font-family: 'Bungee Spice', sans-serif;
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
      font-family: 'Silkscreen', sans-serif;
      margin-left: auto;
    }}
    /* Summary boxes container */
    .summary {{
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 2rem;
    }}

    /* Individual summary box styling */
    .summary-item {{
      font-size: 1.25rem;
      padding: 1rem;
      flex: 1;
      background-color: #fff3cd;  /* Light yellow-orange background */
      border: 2px solid #ffcf40;  /* Yellow border */
      border-radius: 10px;
      min-width: 0px;
      text-align: center;
      color: #5d4037;
      white-space: normal;  /* Allow text to wrap */
      overflow-wrap: break-word; /* Ensures long words break properly */
      display: flex;
      flex-direction: column; /* Stacks content vertically inside the box */
      justify-content: center;
    }}

    /* Main content layout: Chart + Table side-by-side */
    .content {{
      display: flex;
      flex-direction: row;
      justify: space-between;
      gap: 1rem;
    }}

    /* Chart container */
    .plot {{
      flex: 1;
      width: 50%;
      height: 500px;
      box-sizing: border-box;
}}

    .summary-item span {{
      font-weight: normal;  /* Remove bold from span elements */
    }}
    /* Table container (with scroll if needed) */
    .table-container {{
      flex: 1;
      overflow-x: auto;
      box-sizing: border-box;
      width: 50%;
    }}
    .summary-item .label {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;}}

    .table-container h3 {{
      margin-bottom: 0;
    }}

    .table-container table {{
      margin-top: 0.25rem;
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
    @media (max-width: 768px) {{
    .summary {{
      flex-direction: column;  /* Stack summary boxes on mobile */
    }}
    .content {{
      flex-direction: column;  /* Stack chart and table */
    }}
    .plot, .table-container {{
      width: 100%;
    }}}}
    #plot-container > div {{
      width: 50% !important;
      height: 100% !important;
      }}
    @media (max-width: 768px) {{
      .plot,
      #plot-container > div {{
        width: 100% !important;
      }}
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
      <div><strong>Owner:</strong> Lavs</div>
      <div><strong>Last Updated:</strong> {datetime.today().strftime('%d-%m-%Y')}</div>
    </div>
  </div>

  <!-- Summary Boxes -->
  <div class="summary">
    <div class="summary-item">
    <div class="label">
      💰<strong>Total Invested:</strong></div>
      <span>₹{total_invested:,.2f}</span>
    </div>
    <div class="summary-item">
      <div class="label">
      📈<strong>Current Value:</strong> </div>
      <span>₹{current_value:,.2f}</span>
    </div>
    <div class="summary-item">
    <div class="label">
      📊<strong>Portfolio PnL:</strong>
      </div>
      <span class="{pnl_class}">₹{total_pnl:,.2f} ({pnl_percent:.2f}%)</span>
    </div>
  </div>

  <!-- Main Chart + Table Layout -->
  <div class="content">

    <!-- Portfolio PnL Line Chart -->
	<div class="plot" id="plot-container">
		{html_graph}
	</div>
  <div class="table-container">
    <table>
     <tbody id="holdingsTable">
        {portfolio_table}
      </tbody>
   </table>
  </div>
  </div>
</body>
</html>"""

#Write the full HTML to index.html
with open("index.html", "w") as f:
    f.write(html_template)
