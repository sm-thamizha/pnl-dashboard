from datetime import datetime

def generate_html(total_invested, current_value, total_pnl, pnl_percent, pnl_class, html_graph, portfolio_table, daily_pnl=0, daily_pnl_percent=0):
    # Determine classes for PnL styling
    total_pnl_badge_class = "pnl-up arrow-up" if pnl_percent > 0 else "pnl-down arrow-down"
    daily_pnl_badge_class = "pnl-up arrow-up" if daily_pnl >= 0 else "pnl-down arrow-down"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>📈 Portfolio Dashboard</title>
      <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
      <link href="https://fonts.googleapis.com/css2?family=Bungee+Spice&family=Silkscreen:wght@400;700&display=swap" rel="stylesheet">
      <style>
        body {{
          background-color: #1c1c1c;
          color: #ffffff;
          font-family: 'Silkscreen', sans-serif;
          padding: 1rem 2rem 2rem 2rem;
        }}
        h1 {{
          font-family: 'Bungee Spice', sans-serif;
          font-size: 3rem;
          color: #ffffff;
          text-shadow: 2px 2px #00000088;
          margin: 0;
        }}
        .header {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }}
        .info {{
          text-align: right;
        }}
        .main-content {{
          display: flex;
          gap: 1.5rem;
          margin-bottom: 1.5rem;
        }}
        .plot-container {{
          width: 70%;
        }}
        .summary-grid-container {{
          width: 30%;
          display: grid;
          grid-template-columns: 1fr 1fr;
          grid-template-rows: 1fr 1fr;
          gap: 1rem;
        }}
        .summary-item {{
          font-size: 1.1rem;
          padding: 0.75rem;
          background-color: #2a2a2a;
          border: 2px solid #3d3d3d;
          border-radius: 10px;
          color: #ffffff;
          text-align: center;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }}
        .summary-item .value {{
          font-size: 1.5rem;  /* Increased font size for values */
          margin-top: 0.5rem;
        }}
        .summary-item .pnl-wrapper {{
          display: flex;
          flex-direction: column;  /* Changed to column layout */
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
        }}
        .large-summary-item {{
          grid-column: span 2;
        }}
        .table-container {{
          width: 100%;
        }}
        .text-green {{
          color: #4caf50;
        }}
        .text-red {{
          color: #f44336;
        }}
        .section-title {{
          margin: 0.5rem 0;
          font-size: 1.2rem;
          color: #aaaaaa;
        }}

        /* PnL badge styling - matched to table styling */
        .pnl-badge {{
          display: inline-block;
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 12px;
          min-width: 40px;
          text-align: center;
          margin-top: 5px;  /* Added margin top */
        }}
        .pnl-up {{
          background-color: #2f6a3122;  /* Dimmer green background */
          color: #009900;  /* Brighter green text */
        }}
        .pnl-down {{
          background-color: #cc000022;  /* Dimmer red background */
          color: #ff0000;  /* Brighter red text */
        }}
        .arrow-up:before {{
          content: "▲";
          font-size: 9px;
          margin-right: 2px;
        }}
        .arrow-down:before {{
          content: "▼";
          font-size: 9px;
          margin-right: 2px;
        }}

        @media (max-width: 1100px) {{
          .main-content {{
            flex-direction: column;
          }}
          .plot-container {{
            width: 100%;
            margin-bottom: 1rem;
          }}
          .summary-grid-container {{
            width: 100%;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="header">
        <h1>📊 Portfolio Dashboard</h1>
        <div class="info">
          <div><strong>Owner:</strong> SM Thamizha</div>
          <div><strong>Last Updated:</strong> {datetime.today().strftime('%d-%m-%Y')}</div>
        </div>
      </div>

      <div class="main-content">
        <!-- Chart on the left (70%) -->
        <div class="plot-container">
          {html_graph}
        </div>

        <!-- 2x2 Summary grid on the right (30%) -->
        <div class="summary-grid-container">
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
            <div class="value pnl-wrapper">
              <span class="{pnl_class}">₹{total_pnl:,.2f}</span>
              <span class="pnl-badge {total_pnl_badge_class}">{abs(pnl_percent):.1f}%</span>
            </div>
          </div>
          <div class="summary-item">
            <div class="label">📆<strong>Day's<br>PnL:</strong></div>
            <div class="value pnl-wrapper">
              <span class="{'text-green' if daily_pnl >= 0 else 'text-red'}">₹{daily_pnl:,.2f}</span>
              <span class="pnl-badge {daily_pnl_badge_class}">{abs(daily_pnl_percent):.1f}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Table at the bottom -->
      <div class="table-container">
        <div class="section-title">Portfolio Holdings</div>
        {portfolio_table}
      </div>
    </body>
    </html>
    """
    return html_template
