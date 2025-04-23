from datetime import datetime

# HTML generation
def generate_html(total_invested, current_value, total_pnl, pnl_percent, pnl_class, html_graph, portfolio_table):
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
          background-color: #fff8e1;
          color: #3e2723;
          font-family: 'Silkscreen', sans-serif;
          padding: 1rem 2rem 2rem 2rem;
        }}
        h1 {{
          font-family: 'Bungee Spice', sans-serif;
          font-size: 3rem;
          color: #ff6f00;
          text-shadow: 2px 2px #00000044;
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
        .summary {{
          display: flex;
          justify-content: space-between;
          gap: 1rem;
          text-align: center;
          margin-bottom: 1.5rem;
        }}
        .summary-item {{
          font-size: 1.25rem;
          padding: 0.75rem;
          flex: 1;
          background-color: #fff3cd;
          border: 2px solid #ffcf40;
          border-radius: 10px;
          color: #5d4037;
        }}
        .content {{
          display: flex;
          gap: 1.5rem;
          flex-wrap: wrap;
        }}
        .table-container {{
          flex: 0 0 auto;
          min-width: 300px;
        }}
        .plot-container {{
          flex: 1 1 500px;
        }}
        .text-green {{
          color: #2e7d32;
        }}
        .text-red {{
          color: #c62828;
        }}
        
        @media (max-width: 900px) {{
          .content {{
            flex-direction: column;
          }}
          .table-container {{
            margin-bottom: 1.5rem;
            width: 100%;
          }}
          .plot-container {{
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
      <div class="content">
        <div class="table-container">
          {portfolio_table}
        </div>
        <div class="plot-container">
          {html_graph}
        </div>
      </div>
    </body>
    </html>
    """
    return html_template