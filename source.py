import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


#READING DATA FROM HOLDINGS.CSV
holdings_df = pd.read_csv("holdings.csv", dayfirst=True) #Reads csv with DD-MM-YYYY format and stores into pandas dataframe
holdings_df['Date'] = pd.to_datetime(holdings_df['Date'], dayfirst=True) #Converts the DD-MM-YYYY into datetime format and updates itself


#STORING THE HOLDINGS DATA INTO A DICTIONARY FOR EASY USE
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


#DISPLAY HOLDINGS_DICT FOR DEBUG
'''for symbol, entries in holdings_dict.items():
    print(f"Symbol: {symbol}")
    for entry in entries:
        print(f"  Date: {entry['Date']}, Entry: {entry['Entry']}, Quantity: {entry['Quantity']}")
    print("\n")'''

#SET THE START DATE AS FIRST STOCK PURCHASE DATE AND END AS TODAY FOR PNL CALCULATION
start_date = min([datetime.strptime(purchase["Date"], "%Y-%m-%d")
                      for purchases in holdings_dict.values()
                      for purchase in purchases])

end_date = datetime.today()


#FETCHING HISTORICAL PRICE DATA FOR EACH HOLDING
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


#DISPLAY HISTORICAL_DATA FOR DEBUG
'''for symbol, data in historical_data.items():
    for date, close_price in data.items():
        print(f"Symbol: {symbol}, Date: {date}, Close: {close_price}")'''


#COMPUTE DAILY PNL FOR EACH HOLDING
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


#WRITE THE PNL DATA INTO A CSV
df = pd.DataFrame(daily_rows)
df.sort_values(by=["Date", "Symbol"], inplace=True)
print(df)
df.to_csv("holdings_pnl_tracker.csv", index=False)
   

'''--------------------------------------------------PLOTLY CHART OF THE PNL SINCE BEGINNING--------------------------------------------------'''


#READ HOLDING PNL DATA AND CALCULATE SUM FOR DAILY PNL
pnl_file = "holdings_pnl_tracker.csv"
df = pd.read_csv(pnl_file)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
df_total = df.groupby('Date')['PnL'].sum().reset_index()


#X-AXIS TICK MONTHS INSTEAD OF DAYS TO UNCLUTTER
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


#SWITCHING COLOR ON CROSSING ZERO PNL
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


#ADD HOVER INFO FOR EACH TICK
fig.add_scatter(
    x=df_total['Date'],
    y=df_total['PnL'],
    mode='none',
    hovertemplate="Total PnL: %{y:.2f}<br>Date: %{x|%d-%m-%Y}<extra></extra>",
    showlegend=False
)
tick_vals = list(range(int(df_total['PnL'].min()) // 5000 * 5000,
                       int(df_total['PnL'].max()) + 5000, 5000))
tick_text = [f"{v:,.0f}" for v in tick_vals]
fig.update_yaxes(
    tickvals=tick_vals,
    ticktext=tick_text
)


#CHART STYLING
fig.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    yaxis=dict(
    	tick0=0,
    	dtick=5000),
    title="Portfolio PnL",
    height=600,
    template='ggplot2',
    plot_bgcolor='rgba(0, 0, 0, 0)',
    paper_bgcolor='rgba(0, 0, 0, 0)',
    font=dict(
        family="Silkscreen, sans-serif",
        size=12,
        color="#3e2723"
    )
)


#DISPLAY CHART FOR DEBUG
'''fig.show()'''


#CONVERT THE PLOT INTO HTML
html_graph = fig.to_html(include_plotlyjs='cdn', full_html=False)


'''--------------------------------------------------TABLE OF THE HOLDINGS--------------------------------------------------'''


#CALCULATE TOTAL QTY AND INVESTED FOR EACH HOLDING AND THEN OVERALL
portfolio_data = {}

for _, row in holdings_df.iterrows():
    ticker = row['Symbol']
    quantity = row['Quantity']
    price = row['Entry']

    # Aggregate total quantity and total invested for each ticker
    if ticker not in portfolio_data:
        portfolio_data[ticker] = {
            'Total Qty': 0,
            'Total Invested': 0
        }

    portfolio_data[ticker]['Total Qty'] += quantity
    portfolio_data[ticker]['Total Invested'] += round(quantity * price, 2)
	
total_invested = sum([data['Total Invested'] for data in portfolio_data.values()])


#INITIALIZE HTML TABLE
portfolio_table = "<table border='1' style='width:100%; margin-top: 30px; text-align: center; border-collapse: collapse;'>"
portfolio_table += "<tr><th>Ticker</th><th>Quantity</th><th>Avg. Price</th><th>PnL</th></tr>"


#CALCULATE CURRENT VALUE OF EACH HOLDING, TOTAL PNL & PERCENT
current_value = 0
for ticker, data in portfolio_data.items():
    latest_price = df[df['Symbol'] == ticker]['Close Price'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
    current_value += latest_price * data['Total Qty']

total_pnl = current_value - total_invested
pnl_percent = (total_pnl / total_invested) * 100


#COLOR CLASS FOR OVERALL PNL
if total_pnl > 0:
    pnl_class = "text-green"
else:
    pnl_class = "text-red"

#CREATING TABLE ROWS TO DISPLAY
for ticker, data in portfolio_data.items():
    latest_pnl = df[df['Symbol'] == ticker]['PnL'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
    pnl_percentage = (latest_pnl / data['Total Invested']) * 100 if data['Total Invested'] != 0 else 0
    avg_price = data['Total Invested'] / data['Total Qty']
	#COLOR CLASS FOR INDIVIDUAL HOLDING PNL
    if latest_pnl > 0:
        ticker_pnl_class = "text-green"
    else:
        ticker_pnl_class = "text-red"
    portfolio_table += f"<tr><td>{ticker}</td><td>{data['Total Qty']}</td><td>{avg_price:.2f}</td></td><td class='{ticker_pnl_class}'>{latest_pnl} ({pnl_percentage:.2f}%)</td></tr>"


html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>📈 Portfolio Dashboard</title>


  <!--GOOGLE FONTS FOR CUSTOM FONT STYLES-->
  <link href="https://fonts.googleapis.com/css2?family=Bungee+Spice&family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">
  

  <!--PLOTLY.JS FOR INTERACTIVE CHARTS-->
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
	  align-items: center;
	  width: 100%;
	}}

    /* Dashboard title style */
	h1 {{
	  font-family: 'Bungee Spice', sans-serif;
	  font-size: 3rem;
	  color: #ff6f00;
	  text-shadow: 2px 2px #00000044;
	  margin: 0;
	  flex: 1;
	  text-align: center;
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
      gap: 1rem;
      margin-bottom: 2rem;
    }}

    /* Individual summary box styling */
    .summary-item {{
      font-size: 1.25rem;
      padding: 1rem;
      flex: 1;
      background-color: #fff3cd;
      border: 2px solid #ffcf40;
      border-radius: 10px;
      text-align: center;
      color: #5d4037;
      white-space: normal;
      overflow-wrap: break-word;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }}

    /* Main content layout: Chart + Table side-by-side */
    .content {{
      display: flex;
      justify: space-between;
      gap: 1rem;
    }}

    /* Chart container */
    .plot {{
      flex: 0 1 auto;
      height: 800px;
	}}

    /* Table container */
    .table-container {{
      flex: 1 1 auto;
      overflow-x: auto;
      box-sizing: border-box;
    }}

    .summary-item .label {{
      font-weight: bold;
      margin-bottom: 0.5rem;
      display: block;
    }}

    .summary-item .value {{
      font-weight: normal;
    }}

    .table-container h3 {{
      margin-bottom: 0;
    }}

    .table-container table {{
      margin-top: 0.25rem;
    }}

	@media (max-width: 768px) {{
	.summary {{
	  flex-direction: column;
	}}
	.content {{
      flex-direction: column;
	}}
	.plot, .table-container {{
      width: 100%;
	}}
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
      background-color: #ffe082;
      color: #4e2600;
      font-weight: bold;
	  padding: 0.75rem;
    }}
   
    /* Zebra stripe effect for table rows */
    tbody tr:nth-child(even) {{
      background-color: #fffde7;
    }}

    /* Hover effect for rows */
    tbody tr:hover {{
      background-color: #f1f8e9;
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
    <div class="label">💰<strong>Total Invested:</strong></div>
    <div class="value">₹{total_invested:,.2f}</div>
    </div>
    <div class="summary-item">
    <div class="label">📈<strong>Current Value:</strong></div>
    <div class="value">₹{current_value:,.2f}</div>
    </div>
    <div class="summary-item">
    <div class="label">📊<strong>Portfolio PnL:</strong></div>
    <div class="value {pnl_class}">₹{total_pnl:,.2f} ({pnl_percent:.2f}%)</div>
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
