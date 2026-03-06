from flask import Flask, render_template_string
import requests
from bs4 import BeautifulSoup
import re
import yfinance as yf
import time

app = Flask(__name__)

# Nisab Weights
NISAB_GRAMS = 612.35  # 52.5 Tola
NISAB_OZ = 19.69

def get_data():
    results = {'local_gram_price': 0.0, 'global_oz_price': 0.0, 'status': 'Checking...'}
    
    # --- 1. BAJUS Scraping (March 2026 Table Format) ---
    try:
        url = "https://bajus.org/gold-price"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        
        found_local = False
        for row in rows:
            text = row.get_text().lower()
            # Searching for Traditional Silver (সনাতন রূপা)
            if 'silver' in text and ('traditional' in text or 'সনাতন' in text):
                cells = row.find_all('td')
                if cells:
                    raw_val = re.sub(r'[^\d.]', '', cells[-1].get_text())
                    if raw_val:
                        price = float(raw_val)
                        # BAJUS usually gives price per Bhori. 1 Bhori = 11.664g.
                        # If price is high (e.g. 4199), it's Bhori. If low (360), it's Gram.
                        results['local_gram_price'] = price / 11.664 if price > 1000 else price
                        results['status'] = 'Live from BAJUS'
                        found_local = True
                        break
        
        if not found_local:
            # Fallback to March 2026 average if scraper misses the row
            results['local_gram_price'] = 360.0 
            results['status'] = 'Using Market Average'
    except:
        results['local_gram_price'] = 360.0
        results['status'] = 'Service Offline (Average)'

    # --- 2. Global Price ---
    try:
        silver = yf.Ticker("SI=F")
        hist = silver.history(period="1d")
        results['global_oz_price'] = hist['Close'].iloc[-1] if not hist.empty else 0.0
    except:
        pass

    return results

@app.route('/')
def index():
    data = get_data()
    local_nisab = data['local_gram_price'] * NISAB_GRAMS
    global_nisab = data['global_oz_price'] * NISAB_OZ
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    # Terminated triple-quoted string below
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Zakat Monitor</title>
        <style>
            body {{ background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .container {{ background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); width: 350px; text-align: center; }}
            .card {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 12px; margin: 20px 0; text-align: left; border-left: 5px solid #2ecc71; }}
            .nisab-val {{ font-size: 2em; font-weight: bold; color: #2ecc71; }}
            .status {{ font-size: 0.7em; padding: 2px 8px; border-radius: 5px; background: #1e293b; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="status">{data['status']}</span>
            <h2>Zakat Nisab</h2>
            <p style="color:#94a3b8; font-size: 0.8em;">{current_time}</p>
            
            <div class="card">
                <small>BANGLADESH (612.35g)</small>
                <div class="nisab-val">{local_nisab:,.0f} BDT</div>
                <small style="color:#94a3b8">Rate: {data['local_gram_price']:.2f} Tk/g</small>
            </div>

            <div class="card" style="border-left-color: #3498db;">
                <small>GLOBAL (19.69oz)</small>
                <div class="nisab-val" style="color:#3498db">${global_nisab:,.2f}</div>
            </div>
        </div>
        <script>setTimeout(() => location.reload(), 60000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == "__main__":
    app.run()
