from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import time

app = Flask(__name__)

# Zakat Constants
NISAB_GRAMS = 612.35  # 52.5 Tola
NISAB_OZ = 19.69

def get_data():
    results = {'local_gram_price': 0.0, 'global_oz_price': 0.0, 'status': 'Error'}
    
    # --- 1. GET BAJUS LOCAL PRICE ---
    try:
        url = "https://bajus.org/gold-price"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # In 2026, BAJUS uses a table. We look for 'Silver' and 'Traditional'
        # which is the standard for Zakat calculation.
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                text = row.get_text().lower()
                # Zakat is usually based on 'Traditional' (Sonatan) Silver
                if 'silver' in text and 'traditional' in text:
                    # Get the last cell (price per bhori)
                    raw_price = cells[-1].get_text(strip=True)
                    price_per_bhori = float(re.sub(r'[^\d.]', '', raw_price))
                    # 1 Bhori = 11.664 Grams
                    results['local_gram_price'] = price_per_bhori / 11.664
                    results['status'] = 'Live from BAJUS'
                    break
    except Exception as e:
        print(f"Scraping failed: {e}")

    # --- 2. GET YAHOO FINANCE GLOBAL PRICE ---
    try:
        silver = yf.Ticker("SI=F")
        data = silver.history(period="1d")
        if not data.empty:
            results['global_oz_price'] = data['Close'].iloc[-1]
    except:
        pass

    return results

@app.route('/')
def index():
    data = get_data()
    
    # Calculations
    local_nisab = data['local_gram_price'] * NISAB_GRAMS
    global_nisab = data['global_oz_price'] * NISAB_OZ
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    # Note: Using your UI design with the fix
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zakat Nisab Monitor - Bangladesh</title>
        <style>
            :root {{ --bg: #0f172a; --card: rgba(255,255,255,0.05); --text: #fff; --local: #2ecc71; --global: #3498db; }}
            body {{ background: var(--bg); color: var(--text); font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin:0; }}
            .container {{ background: var(--card); padding: 40px; border-radius: 24px; border: 1px solid rgba(255,255,255,0.1); width: 400px; text-align: center; }}
            .card {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 15px; margin: 20px 0; text-align: left; border-left: 5px solid; }}
            .local {{ border-color: var(--local); }}
            .global {{ border-color: var(--global); }}
            .val {{ font-size: 2em; font-weight: 800; margin-top: 5px; color: var(--local); }}
            .global .val {{ color: var(--global); }}
            .status {{ font-size: 0.7em; background: #1e293b; padding: 3px 10px; border-radius: 10px; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Zakat Nisab Monitor</h2>
            <p style="color:#94a3b8">{current_time}</p>
            <span class="status">{data['status']}</span>

            <div class="card local">
                <small>BANGLADESH (612.35g Silver)</small>
                <div class="val">{local_nisab:,.2f} BDT</div>
                <small style="color:#94a3b8">Rate: {data['local_gram_price']:.2f} Tk/gram</small>
            </div>

            <div class="card global">
                <small>GLOBAL (19.69oz Silver)</small>
                <div class="val">${global_nisab:,.2f} USD</div>
            </div>

            <p style="font-size:0.7em; color:#64748b;">Update: 1 Bhori = 11.664g</p>
        </div>
        <script>setTimeout(()=>location.reload(), 60000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template)