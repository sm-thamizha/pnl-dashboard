import pandas as pd
from datetime import datetime, timedelta
from holdings_data import load_holdings, process_holdings, fetch_historical_data, calculate_pnl
from plot_table import generate_pnl_chart, generate_portfolio_table
from html_generator import generate_html

from datetime import datetime, timedelta

# Load and process holdings data from the CSV file
holdings_df = load_holdings("holdings.csv")
holdings_dict = process_holdings(holdings_df)  # Changed from aggregate_holdings to process_holdings

# Dynamically set the start date to the earliest purchase date in the holdings file
earliest_purchase_date = holdings_df['Date'].min()
start_date = earliest_purchase_date

# Set end date to today's date
end_date = datetime.today()

# Fetch historical data from Yahoo Finance (or another source)
historical_data = fetch_historical_data(holdings_dict, start_date, end_date)
print(historical_data)

# Calculate daily PnL
daily_rows = calculate_pnl(holdings_dict, historical_data, start_date, end_date)

# Create a DataFrame for the daily PnL results
df_total = pd.DataFrame(daily_rows)

# Generate tick dates for the chart
tick_dates = [start_date + timedelta(days=i) for i in range(0, (end_date - start_date).days, 30)]
if end_date not in tick_dates:
    tick_dates.append(end_date)

# Create PnL chart
html_graph = generate_pnl_chart(df_total, tick_dates)

# Generate portfolio table
# We need to modify the function call to match our updated function
portfolio_table, total_invested, current_value, total_pnl, pnl_percent, pnl_class, days_pnl_value, days_pnl_percent = generate_portfolio_table(df_total, holdings_df)

# Generate HTML for the dashboard
html = generate_html(
    total_invested=total_invested,
    current_value=current_value,
    total_pnl=total_pnl,
    pnl_percent=pnl_percent,
    pnl_class=pnl_class,
    html_graph=html_graph,
    portfolio_table=portfolio_table,
    daily_pnl=days_pnl_value,
    daily_pnl_percent=days_pnl_percent
)

# Save the generated HTML to a file
with open("index.html", "w") as file:
    file.write(html)
