from datetime import datetime, timedelta

# Updated HTML generation function to match the dark Databox UI style
def generate_html(total_invested, current_value, total_pnl, pnl_percent, pnl_class, html_graph, portfolio_table):
    # Determine appropriate class for positive/negative values
    pnl_direction = "up" if total_pnl >= 0 else "down"
    triangle_class = "triangle-up" if total_pnl >= 0 else "triangle-down"
    
    # Calculate "Day's PnL" based on the last row of data (use total_pnl as fallback)
    # This would need to be calculated in your main.py and passed as a parameter
    days_pnl = total_pnl / 30  # Example calculation - replace with actual daily PnL calculation
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Portfolio Dashboard</title>
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
      <style>
        * {{
          margin: 0;
          padding: 0;
          box-sizing: border-box;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }}
        
        body {{
          background-color: #1a1f35;
          color: #ffffff;
          padding: 20px;
        }}
        
        .dashboard {{
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          grid-gap: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }}
        
        .card {{
          background-color: #232942;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          display: flex;
          flex-direction: column;
        }}
        
        .card-header {{
          font-size: 14px;
          color: #bdc3c7;
          margin-bottom: 15px;
          font-weight: 500;
        }}
        
        .chart-card {{
          grid-column: span 3;
          position: relative;
          padding-bottom: 40px;
        }}
        
        .value-primary {{
          font-size: 48px;
          font-weight: 700;
          margin-bottom: 5px;
        }}
        
        .value-secondary {{
          font-size: 28px;
          font-weight: 600;
          margin-bottom: 5px;
        }}
        
        .comparison {{
          display: flex;
          align-items: center;
          font-size: 14px;
          color: #bdc3c7;
        }}
        
        .chart-container {{
          position: relative;
          width: 100%;
          height: 300px;
          margin-top: 20px;
        }}
        
        .up {{
          color: #4cd964;
        }}
        
        .down {{
          color: #ff3b30;
        }}
        
        .triangle-up {{
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-bottom: 8px solid #4cd964;
          display: inline-block;
          margin-right: 6px;
        }}
        
        .triangle-down {{
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-top: 8px solid #ff3b30;
          display: inline-block;
          margin-right: 6px;
        }}
        
        .table-card {{
          grid-column: span 3;
          overflow-x: auto;
        }}
        
        table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }}
        
        th {{
          text-align: left;
          padding: 12px 15px;
          border-bottom: 1px solid #3a4055;
          color: #bdc3c7;
          font-weight: 500;
        }}
        
        td {{
          padding: 12px 15px;
          border-bottom: 1px solid #3a4055;
        }}
        
        /* Chart Legend */
        .chart-legend {{
          display: flex;
          gap: 20px;
          position: absolute;
          bottom: 10px;
          left: 20px;
        }}
        
        .legend-item {{
          display: flex;
          align-items: center;
          font-size: 14px;
        }}
        
        .legend-color {{
          width: 15px;
          height: 15px;
          margin-right: 8px;
          border-radius: 2px;
        }}
        
        .legend-color.blue {{
          background-color: #00c6ff;
        }}
        
        .legend-color.gray {{
          background-color: #3a4055;
        }}
        
        /* Responsive styles */
        @media (max-width: 900px) {{
          .dashboard {{
            grid-template-columns: 1fr;
          }}
          
          .chart-card, .table-card {{
            grid-column: span 1;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="dashboard">
        <!-- Main chart card -->
        <div class="card chart-card">
          <div class="card-header">Last 30 days ({datetime.today().strftime('%b %d')} - {(datetime.today() - timedelta(days=30)).strftime('%b %d')})</div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
              <div>Amount Invested</div>
              <div class="value-primary">₹ {total_invested:,.2f}</div>
              <div class="comparison">
                <span class="{triangle_class}"></span>
                <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
                <span style="margin-left: 5px;">vs previous period</span>
              </div>
            </div>
          </div>
          
          <!-- Chart -->
          <div class="chart-container">
            {html_graph}
          </div>
        </div>
        
        <!-- Metric cards -->
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Total Invested</div>
          <div class="value-secondary">₹ {total_invested:,.2f}</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
            <span style="margin-left: 5px;">vs previous period</span>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Current Value</div>
          <div class="value-secondary">₹ {current_value:,.2f}</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
            <span style="margin-left: 5px;">vs previous period</span>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Day's PnL</div>
          <div class="value-secondary">₹ {days_pnl:,.2f}</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
            <span style="margin-left: 5px;">vs previous day</span>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Portfolio PnL</div>
          <div class="value-secondary">₹ {total_pnl:,.2f}</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
            <span style="margin-left: 5px;">vs previous period</span>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Return %</div>
          <div class="value-secondary">{pnl_percent:.2f}%</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent/2):.2f}%</span>
            <span style="margin-left: 5px;">vs previous period</span>
          </div>
        </div>
        
        <div class="card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div>Annual Return</div>
          <div class="value-secondary">{pnl_percent * 12:.2f}%</div>
          <div class="comparison">
            <span class="{triangle_class}"></span>
            <span class="{pnl_direction}">{abs(pnl_percent):.2f}%</span>
            <span style="margin-left: 5px;">vs previous period</span>
          </div>
        </div>
        
        <!-- Portfolio table -->
        <div class="card table-card">
          <div class="card-header">Last 30 days ({(datetime.today() - timedelta(days=30)).strftime('%b %d')} - {datetime.today().strftime('%b %d')})</div>
          <div style="margin-bottom: 15px;">Campaign Performance Overview</div>
          {portfolio_table}
        </div>
      </div>
    </body>
    </html>
    """
    return html_template
