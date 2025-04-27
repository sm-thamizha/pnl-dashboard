import plotly.graph_objects as go
import pandas as pd
from datetime import timedelta

# Generate Plotly chart of PnL with dark theme
def generate_pnl_chart(df_total, tick_dates):
    fig = go.Figure()
    df_total.sort_values(by='Date', inplace=True)
    df_total.reset_index(drop=True, inplace=True)

    # Group by date and sum PnL values to get daily totals
    daily_pnl = df_total.groupby('Date')['PnL'].sum().reset_index()
    daily_pnl['Date'] = pd.to_datetime(daily_pnl['Date'])
    daily_pnl = daily_pnl.sort_values('Date')

    # Create a line chart with the blue line seen in the reference
    fig.add_trace(go.Scatter(
        x=daily_pnl['Date'],
        y=daily_pnl['PnL'],
        mode='lines',
        line=dict(color='#00c6ff', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 198, 255, 0.1)',
        name='PnL'
    ))

    # Add an invisible scatter trace for hover information
    fig.add_scatter(
        x=daily_pnl['Date'],
        y=daily_pnl['PnL'],
        mode='none',
        hovertemplate="₹%{y:,.2f}<br>%{x|%d %b %Y}<extra></extra>",
        showlegend=False
    )

    # Format x-axis
    tick_vals = [pd.to_datetime(date) for date in tick_dates]
    tick_text = [date.strftime("%d") for date in tick_vals]  # Just show day numbers

    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        tickangle=0,
        gridcolor='rgba(58, 64, 85, 0.3)',
        ticks='outside',
        ticklen=4,
        tickfont=dict(color='#bdc3c7', size=10),
        showgrid=False,
        zeroline=False
    )

    # Format y-axis
    max_abs_pnl = max(abs(daily_pnl['PnL'].max()), abs(daily_pnl['PnL'].min()))
    y_step = 5000 if max_abs_pnl > 10000 else 2000
    tick_vals = list(range(int(-max_abs_pnl * 1.1) // y_step * y_step,
                         int(max_abs_pnl * 1.1) // y_step * y_step + y_step,
                         y_step))

    # Function to format y-axis ticks in abbreviated format (k for thousands)
    def format_tick(val):
        if abs(val) >= 1000:
            return f"{val/1000:.0f}k"
        return str(val)

    fig.update_yaxes(
        tickvals=tick_vals,
        ticktext=[format_tick(val) for val in tick_vals],
        gridcolor='rgba(58, 64, 85, 0.3)',
        zeroline=True,
        zerolinecolor='rgba(255, 255, 255, 0.3)',
        zerolinewidth=1,
        tickfont=dict(color='#bdc3c7', size=10)
    )

    # Update layout for dark theme
    fig.update_layout(
        margin=dict(t=0, b=0, l=40, r=20),
        height=300,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        showlegend=False,
        hovermode="x unified"
    )

    # Return HTML 
    chart_html = fig.to_html(include_plotlyjs=False, full_html=False, config={'responsive': True, 'displayModeBar': False})
    
    return chart_html

# Generate the portfolio table with dark theme
def generate_portfolio_table(df, holdings_df):
    # Create portfolio data dictionary from holdings
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

    # Calculate total portfolio stats
    total_invested = sum([data['Total Invested'] for data in portfolio_data.values()])
    current_value = 0

    # Generate HTML table
    table_html = """
    <table class="portfolio-table">
      <thead>
        <tr>
          <th>Campaign</th>
          <th>Quantity</th>
          <th>vs prev</th>
          <th>Avg Price</th>
          <th>vs prev</th>
          <th>Current Price</th>
          <th>vs prev</th>
          <th>PnL</th>
          <th>vs prev</th>
          <th>PnL %</th>
          <th>vs prev</th>
        </tr>
      </thead>
      <tbody>
    """

    # Create table rows for each holding
    for ticker, data in portfolio_data.items():
        # Get latest price and calculate metrics
        latest_price = df[df['Symbol'] == ticker]['Close Price'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
        ticker_current_value = latest_price * data['Total Qty']
        current_value += ticker_current_value
        avg_price = data['Total Invested'] / data['Total Qty'] if data['Total Qty'] > 0 else 0
        latest_pnl = df[df['Symbol'] == ticker]['PnL'].iloc[-1] if not df[df['Symbol'] == ticker].empty else 0
        pnl_percentage = (latest_pnl / data['Total Invested']) * 100 if data['Total Invested'] > 0 else 0

        # Mock data for previous period comparisons (you would replace this with actual data)
        prev_qty = data['Total Qty'] * 0.9  # 10% less
        prev_avg_price = avg_price * 0.98  # 2% less
        prev_curr_price = latest_price * 0.95  # 5% less
        prev_pnl = latest_pnl * 0.8  # 20% less
        prev_pnl_pct = pnl_percentage * 0.9  # 10% less

        # Calculate percentage changes
        qty_change_pct = ((data['Total Qty'] - prev_qty) / prev_qty) * 100 if prev_qty != 0 else 0
        avg_price_change_pct = ((avg_price - prev_avg_price) / prev_avg_price) * 100 if prev_avg_price != 0 else 0
        curr_price_change_pct = ((latest_price - prev_curr_price) / prev_curr_price) * 100 if prev_curr_price != 0 else 0
        pnl_change_pct = ((latest_pnl - prev_pnl) / prev_pnl) * 100 if prev_pnl != 0 else 0
        pnl_pct_change_pct = ((pnl_percentage - prev_pnl_pct) / prev_pnl_pct) * 100 if prev_pnl_pct != 0 else 0

        # Helper function to generate comparison cell
        def comp_cell(value, prev_value):
            change_pct = ((value - prev_value) / prev_value) * 100 if prev_value != 0 else 0
            direction = "up" if change_pct >= 0 else "down"
            triangle = "triangle-up" if change_pct >= 0 else "triangle-down"
            return f'<td><span class="{triangle}"></span> <span class="{direction}">{abs(change_pct):.0f}%</span></td>'

        # Add row to table
        table_html += f"""
        <tr>
          <td>{ticker}</td>
          <td>{data['Total Qty']}</td>
          {comp_cell(data['Total Qty'], prev_qty)}
          <td>₹ {avg_price:.2f}</td>
          {comp_cell(avg_price, prev_avg_price)}
          <td>₹ {latest_price:.2f}</td>
          {comp_cell(latest_price, prev_curr_price)}
          <td>₹ {latest_pnl:.2f}</td>
          {comp_cell(latest_pnl, prev_pnl)}
          <td>{pnl_percentage:.1f}%</td>
          {comp_cell(pnl_percentage, prev_pnl_pct)}
        </tr>
        """

    table_html += """
      </tbody>
    </table>
    """

    # Calculate total portfolio performance
    total_pnl = current_value - total_invested
    pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
    pnl_class = "up" if total_pnl > 0 else "down"

    return table_html, total_invested, current_value, total_pnl, pnl_percent, pnl_class
