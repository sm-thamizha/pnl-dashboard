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
                line=dict(color='#f44336' if y0 < 0 else '#4caf50', width=3),
                fill='tozeroy',
                fillcolor='rgba(244, 67, 54, 0.3)' if y0 < 0 else 'rgba(76, 175, 80, 0.3)',
                showlegend=False,
                hoverinfo='skip'
            )

            # Add second segment with fill
            fig.add_scatter(
                x=[crossing_time, x1],
                y=[0, y1],
                mode='lines',
                line=dict(color='#4caf50' if y1 >= 0 else '#f44336', width=3),
                fill='tozeroy',
                fillcolor='rgba(76, 175, 80, 0.3)' if y1 >= 0 else 'rgba(244, 67, 54, 0.3)',
                showlegend=False,
                hoverinfo='skip'
            )
        else:
            # Add single segment with appropriate color and fill
            line_color = '#4caf50' if y0 >= 0 and y1 >= 0 else '#f44336'
            fill_color = 'rgba(76, 175, 80, 0.3)' if y0 >= 0 and y1 >= 0 else 'rgba(244, 67, 54, 0.3)'

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
        gridcolor='rgba(150, 150, 150, 0.15)',
        color='#ffffff',
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
        gridcolor='rgba(150, 150, 150, 0.15)',
        zeroline=True,
        zerolinecolor='#777777',
        zerolinewidth=1,
        color='#ffffff'
    )

    # Update layout with reduced bottom margin
    fig.update_layout(
        title={
            'text': "CUMULATIVE PNL",
            'font': {'family': "Silkscreen, sans-serif", 'size': 16, 'color': "#ffffff", 'weight': 'bold'},
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.98,
            'yanchor': 'top'
        },
        height=500,
        # Reduced bottom margin from 60 to 25
        margin=dict(t=30, b=25, l=50, r=20),
        template='plotly_dark',
        plot_bgcolor='#2a2a2a',
        paper_bgcolor='#2a2a2a',
        font=dict(family="Silkscreen, sans-serif", size=12, color="#ffffff"),
        hovermode="x unified"
    )

    # Return HTML with a wrapper div to add custom styling for curved corners
    chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})

    # Add wrapper with custom styling for the plot
    styled_chart_html = f"""
    <div class="chart-wrapper">
      <style>
        .chart-wrapper {{
          border: 2px solid #3d3d3d;
          border-radius: 8px;
          overflow: hidden;
          padding: 8px 8px 0px 8px; /* Reduced bottom padding to 0px */
          background-color: #2a2a2a;
        }}
      </style>
      {chart_html}
    </div>
    """

    return styled_chart_html

# Generate the portfolio table
# Generate the portfolio table
def generate_portfolio_table(df, holdings_df):
    # Create portfolio data dictionary from holdings
    portfolio_data = {}
    for _, row in holdings_df.iterrows():
        ticker = row['Symbol']
        quantity = row['Quantity']
        price = row['Entry']
        date = row.get('Date', None)  # Get purchase date if available

        # Aggregate total quantity and total invested for each ticker
        if ticker not in portfolio_data:
            portfolio_data[ticker] = {
                'Total Qty': 0,
                'Total Invested': 0,
                'First Purchase Date': None,
                'Price History': []
            }
        portfolio_data[ticker]['Total Qty'] += quantity
        portfolio_data[ticker]['Total Invested'] += round(quantity * price, 2)
        if date:
            if portfolio_data[ticker]['First Purchase Date'] is None or date < portfolio_data[ticker]['First Purchase Date']:
                portfolio_data[ticker]['First Purchase Date'] = date

    # Calculate total portfolio stats
    total_invested = sum([data['Total Invested'] for data in portfolio_data.values()])
    current_value = 0
    days_pnl_value = 0  # Initialize day's PnL value

    # Extract price history for each ticker - ensure we're using compatible date types
    for ticker in portfolio_data:
        ticker_df = df[df['Symbol'] == ticker].copy()
        if not ticker_df.empty:
            # Use full price history if no purchase date is available
            if portfolio_data[ticker]['First Purchase Date'] is None:
                portfolio_data[ticker]['Price History'] = ticker_df['Close Price'].tolist()
            else:
                # Ensure both dates are in the same format (pandas Timestamp)
                purchase_date = pd.to_datetime(portfolio_data[ticker]['First Purchase Date'])
                # Make sure Date column in df is also datetime
                if 'Date' in ticker_df.columns:
                    ticker_df['Date'] = pd.to_datetime(ticker_df['Date'])
                    # Filter price history from purchase date onward
                    filtered_df = ticker_df[ticker_df['Date'] >= purchase_date]
                    if not filtered_df.empty:
                        portfolio_data[ticker]['Price History'] = filtered_df['Close Price'].tolist()
                    else:
                        portfolio_data[ticker]['Price History'] = ticker_df['Close Price'].tolist()
                else:
                    portfolio_data[ticker]['Price History'] = ticker_df['Close Price'].tolist()

            # Calculate day's change for this ticker
            # Check if 'Previous Close' is available in the dataframe
            if 'Previous Close' in ticker_df.columns and not ticker_df.empty:
                latest_close = ticker_df['Close Price'].iloc[-1]
                previous_close = ticker_df['Previous Close'].iloc[-1]
                days_change = latest_close - previous_close
                days_pnl_value += days_change * portfolio_data[ticker]['Total Qty']
            elif len(ticker_df) >= 2:  # If we have at least 2 data points
                latest_close = ticker_df['Close Price'].iloc[-1]
                previous_close = ticker_df['Close Price'].iloc[-2]
                days_change = latest_close - previous_close
                days_pnl_value += days_change * portfolio_data[ticker]['Total Qty']

    # Generate HTML table
    table_html = """
    <table class="portfolio-table">
      <thead>
        <tr>
          <th>TICKER</th>
          <th>QUANTITY</th>
          <th>AVERAGE</th>
          <th>INVESTED</th>
          <th>CURRENT</th>
          <th>PNL</th>
          <th>TREND</th>
        </tr>
      </thead>
      <tbody>
    """

    # Enhanced CSS with improved styling
    table_html += """
    <style>
      .portfolio-table {
        border-collapse: separate;
        border-spacing: 0;
        border: 2px solid #3d3d3d;
        border-radius: 8px;
        overflow: hidden;
        width: 100%;
        table-layout: auto;
      }

      .portfolio-table th {
        padding: 30px 15px;
        background-color: #3d3d3d;
        border-right: 1px solid #555;
        font-weight: bold;
        white-space: nowrap;
        text-transform: uppercase;
        letter-spacing: 1px;
      }

      .portfolio-table th:last-child {
        border-right: none;
      }

      .portfolio-table td {
        padding: 30px 15px;
        border-right: 1px solid #444;
        border-bottom: 1px solid #444;
        white-space: nowrap;
        text-align: center;
      }

      .portfolio-table td:last-child {
        border-right: none;
        width: 100%;  /* Make sparkline column take maximum available width */
        padding: 0;   /* Remove padding for sparkline cells */
      }

      .portfolio-table tr:last-child td {
        border-bottom: none;
      }

      .portfolio-table tbody tr {
        background-color: #2a2a2a;
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
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 12px;
        min-width: 40px;
        text-align: center;
        margin-left: 8px;
      }

      .pnl-up {
        background-color: #2f6a3122;  /* Dimmer green background */
        color: #009900;  /* Brighter green text */
      }

      .pnl-down {
        background-color: #cc000022;  /* Dimmer red background */
        color: #ff0000;  /* Brighter red text */
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
        color: #4caf50;
      }

      .text-red {
        color: #f44336;
      }

      /* Sparkline styling */
      .sparkline-container {
        position: relative;
        width: 100%;
        height: 100%;
        display: block;
      }

      .sparkline {
        stroke: #f44336;
        stroke-width: 0.5;
        fill: none;
      }

      .sparkline.positive {
        stroke: #4caf50;
      }

      .reference-line {
        stroke: #888;
        stroke-width: 1;
        stroke-dasharray: 2, 2;
      }

      /* Ensure sparkline SVG takes full width and height */
      .sparkline-svg {
        width: 100%;
        height: 80px;
        display: block;
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
        latest_pnl = ticker_current_value - data['Total Invested']
        pnl_percentage = (latest_pnl / data['Total Invested']) * 100 if data['Total Invested'] > 0 else 0

        # Determine color class for PnL
        ticker_pnl_class = "text-green" if latest_pnl > 0 else "text-red"
        badge_class = "pnl-up arrow-up" if pnl_percentage > 0 else "pnl-down arrow-down"

        # Create sparkline SVG
        price_history = data['Price History']
        sparkline_svg = create_sparkline(price_history, avg_price, latest_price > avg_price)

        # Add row to table with PnL value and percentage badge together in the same column
        table_html += f"""
        <tr>
          <td>{ticker}</td>
          <td>{data['Total Qty']}</td>
          <td>₹{avg_price:.2f}</td>
          <td>₹{data['Total Invested']:.2f}</td>
          <td>₹{ticker_current_value:.2f}</td>
          <td>
            <span class="{ticker_pnl_class}">₹{latest_pnl:.2f}</span>
            <span class="pnl-badge {badge_class}">{abs(pnl_percentage):.1f}%</span>
          </td>
          <td class="sparkline-cell">{sparkline_svg}</td>
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

    # Calculate day's PnL percentage (relative to total invested)
    days_pnl_percent = (days_pnl_value / total_invested) * 100 if total_invested > 0 else 0

    return table_html, total_invested, current_value, total_pnl, pnl_percent, pnl_class, days_pnl_value, days_pnl_percent

def create_sparkline(prices, avg_price, is_positive):
    """Create an SVG sparkline with a reference line at the average price"""
    if not prices or len(prices) < 2:
        # Return a horizontal dashed line if no data
        return """
        <div class="sparkline-container">
          <svg class="sparkline-svg" preserveAspectRatio="none" viewBox="0 0 100 40">
            <line x1="0" y1="20" x2="100" y2="20" class="reference-line" />
          </svg>
        </div>
        """

    # Set dimensions
    width = 100
    height = 40
    padding_x = 0  # Remove horizontal padding to use full width
    padding_y = 5
    drawable_width = width
    drawable_height = height - 2 * padding_y

    # Calculate min and max for scaling
    min_price = min(prices + [avg_price]) * 0.95  # Add padding
    max_price = max(prices + [avg_price]) * 1.05
    price_range = max_price - min_price if max_price > min_price else 1

    # Scale prices to fit in the drawable area
    def scale_y(price):
        if price_range == 0:
            return padding_y + drawable_height / 2
        return padding_y + drawable_height - ((price - min_price) / price_range * drawable_height)

    # Generate points for the sparkline
    points = []
    for i, price in enumerate(prices):
        x = (i / (len(prices) - 1)) * width
        y = scale_y(price)
        points.append(f"{x},{y}")

    # Calculate y position for average price reference line
    avg_y = scale_y(avg_price)

    # Determine stroke color class based on performance
    stroke_class = "positive" if is_positive else ""

    # Create SVG ensuring it fills the entire cell
    svg = f"""
    <div class="sparkline-container">
      <svg class="sparkline-svg" preserveAspectRatio="none" viewBox="0 0 {width} {height}">
        <line x1="0" y1="{avg_y}" x2="{width}" y2="{avg_y}" class="reference-line" />
        <polyline points="{' '.join(points)}" class="sparkline {stroke_class}" />
      </svg>
    </div>
    """

    return svg
