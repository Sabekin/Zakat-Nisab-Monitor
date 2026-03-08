from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import time

app = Flask(__name__)

# Constants
NISAB_GRAMS = 612.35
NISAB_OZ = 19.69
USD_TO_BDT = 120.0  # Fallback exchange rate

def get_local_silver():
    """Targeted scraper for BAJUS (Bangladesh)"""
    try:
        url = "https://bajus.org/gold-price"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }
        # Timeout added to prevent Vercel from hanging
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'lxml')
        # PricePoka logic: Look for specific table rows
        rows = soup.select('table tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                text = row.get_text().lower()
                # Specific check for Silver (Traditional/Sanatan)
                if 'silver' in text and ('traditional' in text or 'sanatan' in text):
                    price_text = cells[-1].get_text(strip=True)
                    return float(re.sub(r'[^\d.]', '', price_text))
    except Exception as e:
        print(f"Local Scrape Error: {e}")
    return None

def get_global_silver():
    """Fetches global price via Yahoo Finance (Reliable API-like source)"""
    try:
        silver = yf.Ticker("SI=F")
        # fast_info is quicker for serverless functions
        price = silver.fast_info.last_price
        return price
    except:
        try:
            # Fallback to history if fast_info is blocked
            data = silver.history(period="1d")
            return data['Close'].iloc[-1]
        except:
            return None

@app.route('/')
def index():
    local_price = get_local_silver()
    global_price = get_global_silver()
    
    # Logic: If local price fails, estimate from global
    display_local = local_price if local_price else (global_price * 0.035274 * USD_TO_BDT if global_price else 0)
    display_global = global_price if global_price else 0
    
    local_nisab = display_local * NISAB_GRAMS
    global_nisab = display_global * NISAB_OZ
    
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    # CSS with Frosted Glass effect similar to modern UI projects
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zakat Nisab Monitor</title>
        <style>
            :root {{
                --accent: #00d1b2;
                --bg: #0a0b10;
                --glass: rgba(255, 255, 255, 0.03);
                --border: rgba(255, 255, 255, 0.1);
            }}
            body {{
                background: var(--bg);
                color: white;
                font-family: 'Inter', system-ui, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }}
            .container {{
                background: var(--glass);
                backdrop-filter: blur(20px);
                border: 1px solid var(--border);
                padding: 40px;
                border-radius: 24px;
                width: 90%;
                max-width: 450px;
                text-align: center;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            }}
            .status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                background: { 'rgba(0, 209, 178, 0.1)' if local_price else 'rgba(255, 68, 68, 0.1)' };
                color: { '#00d1b2' if local_price else '#ff4444' };
                margin-bottom: 20px;
            }}
            .price-grid {{
                display: grid;
                gap: 20px;
                margin: 20px 0;
            }}
            .price-card {{
                background: rgba(255,255,255,0.02);
                border: 1px solid var(--border);
                padding: 20px;
                border-radius: 16px;
                text-align: left;
            }}
            .label {{ color: #888; font-size: 13px; text-transform: uppercase; }}
            .value {{ font-size: 24px; font-weight: 700; margin: 5px 0; color: var(--accent); }}
            .nisab {{ font-size: 32px; font-weight: 800; letter-spacing: -1px; }}
            .footer {{ color: #555; font-size: 12px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status">● { 'Live Local Data' if local_price else 'Global Market Estimate' }</div>
            <h2 style="margin:0">Nisab Monitor</h2>
            <p style="color:#666; font-size: 14px;">{current_time}</p>

            <div class="price-grid">
                <div class="price-card">
                    <div class="label">Bangladesh (1g Silver)</div>
                    <div class="value">{display_local:,.2f} BDT</div>
                    <div class="label">Nisab (612.35g)</div>
                    <div class="nisab" style="color:#00d1b2">{local_nisab:,.0f} BDT</div>
                </div>

                <div class="price-card">
                    <div class="label">Global Market (1oz)</div>
                    <div class="value">${display_global:,.2f} USD</div>
                    <div class="label">Nisab (19.69oz)</div>
                    <div class="nisab" style="color:#3498db">${global_nisab:,.2f} USD</div>
                </div>
            </div>
            
            <div class="footer">
                Data sources: BAJUS & Yahoo Finance<br>
                &copy; 2026 Sabekin Muhammad
            </div>
        </div>
        <script>setTimeout(() => location.reload(), 60000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template)

app = app
