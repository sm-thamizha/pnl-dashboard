import plotly.graph_objects as go
import pandas as pd

# Generate Plotly chart of PnL
def generate_pnl_chart(df_total, tick_dates):
    fig = go.Figure()
    df_total.sort_values(by='Date', inplace=True)
    df_total.reset_index(drop=True, inplace=True)

    # Group by date and sum PnL values to get daily totals
    daily_pnl = df_total.groupby('Date')['PnL'].sum().reset_index()
    daily_pnl['Date'] = pd.to_datetime(daily_pnl['Date'])
    daily_pnl = daily_pnl.sort_values('Date')

    # For each segment between consecutive points, determine color based on value
    for i in range(1, len(daily_pnl)):
        x0 = daily_pnl['Date'].iloc[i-1]
        x1 = daily_pnl['Date'].iloc[i]
        y0 = daily_pnl['PnL'].iloc[i-1]
        y1 = daily_pnl['PnL'].iloc[i]

        # If the line crosses zero, we need to split it
        if (y0 < 0 and y1 >= 0) or (y0 >= 0 and y1 < 0):
            # Calculate where the line crosses zero
            crossing_ratio = abs(y0) / (abs(y0) + abs(y1))
            crossing_time = x0 + (x1 - x0) * crossing_ratio

            # Add first segment with fill
            fig.add_scatter(
                x=[x0, crossing_time],
                y=[y0, 0],
                mode='lines',
                line=dict(color='red' if y0 < 0 else 'green', width=3),
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.3)' if y0 < 0 else 'rgba(0, 128, 0, 0.3)',
                showlegend=False,
                hoverinfo='skip'
            )

            # Add second segment with fill
            fig.add_scatter(
                x=[crossing_time, x1],
                y=[0, y1],
                mode='lines',
                line=dict(color='green' if y1 >= 0 else 'red', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 128, 0, 0.3)' if y1 >= 0 else 'rgba(255, 0, 0, 0.3)',
                showlegend=False,
                hoverinfo='skip'
            )
        else:
            # Add single segment with appropriate color and fill
            line_color = 'green' if y0 >= 0 and y1 >= 0 else 'red'
            fill_color = 'rgba(0, 128, 0, 0.3)' if y0 >= 0 and y1 >= 0 else 'rgba(255, 0, 0, 0.3)'

            fig.add_scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(color=line_color, width=3),
                fill='tozeroy',
                fillcolor=fill_color,
                showlegend=False,
                hoverinfo='skip'
            )

    # Add an invisible scatter trace for hover information
    fig.add_scatter(
        x=daily_pnl['Date'],
        y=daily_pnl['PnL'],
        mode='none',
        hovertemplate="₹%{y:,.2f}<br>%{x|%d %b %Y}<extra></extra>",
        showlegend=False
    )

    # Format x-axis with month labels and abbreviated year format
    tick_vals = [pd.to_datetime(date) for date in tick_dates]

    # Custom function to format date tick labels with abbreviated years
    def custom_date_format(date):
        date_obj = pd.to_datetime(date)
        month = date_obj.strftime("%b")
        year = date_obj.strftime("%y")
        return f"{month} '{year}"

    # Generate custom tick labels
    tick_text = [custom_date_format(date) for date in tick_vals]

    fig.update_xaxes(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        tickangle=0,
        gridcolor='rgba(200, 200, 200, 0.2)',
        # Move ticks closer to axis
        ticks='outside',
        ticklen=4
    )

    # Format y-axis
    max_abs_pnl = max(abs(daily_pnl['PnL'].max()), abs(daily_pnl['PnL'].min()))
    y_step = 5000 if max_abs_pnl > 10000 else 2000
    tick_vals = list(range(int(-max_abs_pnl * 1.1) // y_step * y_step,
                         int(max_abs_pnl * 1.1) // y_step * y_step + y_step,
                         y_step))

    fig.update_yaxes(
        tickvals=tick_vals,
        tickformat="₹{:,.0f}",
        gridcolor='rgba(200, 200, 200, 0.2)',
        zeroline=True,
        zerolinecolor='black',
        zerolinewidth=1
    )

    # Update layout with reduced bottom margin
    fig.update_layout(
        title={
            'text': "CUMULATIVE PNL",
            'font': {'family': "Silkscreen, sans-serif", 'size': 16, 'color': "#333333", 'weight': 'bold'},
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.98,
            'yanchor': 'top'
        },
        height=500,
        # Reduced bottom margin from 60 to 25
        margin=dict(t=30, b=25, l=50, r=20),
        template='plotly_white',
        plot_bgcolor='rgba(255, 248, 225, 0.5)',
        paper_bgcolor='rgba(255, 248, 225, 0.5)',
        font=dict(family="Silkscreen, sans-serif", size=12, color="#333333"),
        hovermode="x unified"
    )

    # Return HTML with a wrapper div to add custom styling for curved corners
    chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
    
    # Add wrapper with custom styling for the plot
    styled_chart_html = f"""
    <div class="chart-wrapper">
      <style>
        .chart-wrapper {{
          border: 2px solid #ffcf40;
          border-radius: 8px;
          overflow: hidden;
          padding: 8px 8px 0px 8px; /* Reduced bottom padding to 0px */
          background-color: rgba(255, 248, 225, 0.5);
        }}
      </style>
      {chart_html}
    </div>
    """
    
    return styled_chart_html

# Generate the portfolio table
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
          <th>TICKER</th>
          <th>QTY</th>
          <th>AVG. PRICE</th>
          <th>PNL</th>
        </tr>
      </thead>
      <tbody>
    """

    # Enhanced CSS with removed borders and improved styling
    table_html += """
    <style>
      .portfolio-table {
        border-collapse: separate;
        border-spacing: 0;
        border: 2px solid #ffcf40;
        border-radius: 8px;
        overflow: hidden;
        width: 100%;
      }

      .portfolio-table th {
        padding: 10px 15px;
        background-color: #f8e28b;
        border: none;
        font-weight: bold;
      }

      .portfolio-table td {
        padding: 10px 15px;
        border: none;
        border-bottom: 1px solid #ddd;
      }

      .portfolio-table tr:last-child td {
        border-bottom: none;
      }

      /* Rounded corners for first and last cells in header row */
      .portfolio-table thead tr th:first-child {
        border-top-left-radius: 6px;
      }

      .portfolio-table thead tr th:last-child {
        border-top-right-radius: 6px;
      }

      /* Rounded corners for first and last cells in last row */
      .portfolio-table tbody tr:last-child td:first-child {
        border-bottom-left-radius: 6px;
      }

      .portfolio-table tbody tr:last-child td:last-child {
        border-bottom-right-radius: 6px;
      }

      .pnl-badge {
        display: inline-block;
        padding: 1px 4px;
        border-radius: 3px;
        font-size: 11px;
        min-width: 40px;
        text-align: center;
        color: white;
        font-weight: bold;
        margin-left: 8px;
      }

      .pnl-up {
        background-color: #2e7d32;
      }

      .pnl-down {
        background-color: #c62828;
      }

      .arrow-up:before {
        content: "▲";
        font-size: 9px;
        margin-right: 2px;
      }

      .arrow-down:before {
        content: "▼";
        font-size: 9px;
        margin-right: 2px;
      }

      .text-green {
        color: #2e7d32;
      }

      .text-red {
        color: #c62828;
      }
    </style>
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

        # Determine color class for PnL
        ticker_pnl_class = "text-green" if latest_pnl > 0 else "text-red"
        badge_class = "pnl-up arrow-up" if pnl_percentage > 0 else "pnl-down arrow-down"

        # Add row to table with PnL value and percentage badge together in the same column
        table_html += f"""
        <tr>
          <td>{ticker}</td>
          <td>{data['Total Qty']}</td>
          <td>₹{avg_price:.2f}</td>
          <td>
            <span class="{ticker_pnl_class}">₹{latest_pnl:.2f}</span>
            <span class="pnl-badge {badge_class}">{abs(pnl_percentage):.1f}%</span>
          </td>
        </tr>
        """

    table_html += """
      </tbody>
    </table>
    """

    # Calculate total portfolio performance
    total_pnl = current_value - total_invested
    pnl_percent = (total_pnl / total_invested) * 100 if total_invested > 0 else 0
    pnl_class = "text-green" if total_pnl > 0 else "text-red"

    return table_html, total_invested, current_value, total_pnl, pnl_percent, pnl_class