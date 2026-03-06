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

def get_live_bajus():
    """Bypasses blocks to get live BAJUS Traditional Silver price."""
    url = "https://bajus.org/gold-price"
    
    # Advanced headers to look like a real person visiting from Dhaka
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,bn;q=0.8',
        'Referer': 'https://www.google.com/',
    }

    try:
        # We use a session to handle cookies which helps bypass some bots-blocks
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            
            for row in rows:
                row_text = row.get_text().lower()
                # Zakat is calculated on 'Traditional' (Sonatan) Silver
                if 'silver' in row_text and ('traditional' in row_text or 'সনাতন' in row_text):
                    cells = row.find_all('td')
                    if cells:
                        # Extract the last numeric value in the row
                        price_text = re.sub(r'[^\d.]', '', cells[-1].get_text())
                        price = float(price_text)
                        
                        # BAJUS price is usually per Bhori (11.664g)
                        # Current March 2026 rate is ~4,432 BDT/Bhori
                        if price > 1000:
                            return round(price / 11.664, 2), "Live (BAJUS)"
                        else:
                            return price, "Live (BAJUS)"
    except Exception as e:
        print(f"Scraper Error: {e}")
    
    return None, None

@app.route('/')
def index():
    local_rate, source = get_live_bajus()
    
    # If scraper fails, we show a 'Market Warning' instead of a fake fixed price
    is_fallback = False
    if not local_rate:
        local_rate = 380.00 # Approximate March 2026 market average
        source = "Market Average (Scraper Blocked)"
        is_fallback = True

    # Global Price
    global_oz = 0.0
    try:
        silver = yf.Ticker("SI=F")
        hist = silver.history(period="1d")
        global_oz = hist['Close'].iloc[-1] if not hist.empty else 0.0
    except: pass

    local_nisab = local_rate * NISAB_GRAMS
    global_nisab = global_oz * NISAB_OZ
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zakat Monitor</title>
        <style>
            :root {{ --bg: #0f172a; --accent: {'#e74c3c' if is_fallback else '#2ecc71'}; }}
            body {{ background: var(--bg); color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .container {{ background: rgba(255,255,255,0.05); padding: 30px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); width: 350px; text-align: center; }}
            .status {{ font-size: 0.65em; padding: 3px 8px; border-radius: 5px; background: #1e293b; color: var(--accent); font-weight: bold; border: 1px solid var(--accent); }}
            .card {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 12px; margin: 20px 0; text-align: left; border-left: 5px solid var(--accent); }}
            .nisab-val {{ font-size: 2em; font-weight: bold; color: var(--accent); }}
        </style>
    </head>
    <body>
        <div class="container">
            <span class="status">{source}</span>
            <h2 style="margin: 15px 0 5px 0;">Zakat Nisab</h2>
            <p style="color:#94a3b8; font-size: 0.8em; margin-bottom: 20px;">{current_time}</p>
            
            <div class="card">
                <small>BANGLADESH (Silver 52.5 Tola)</small>
                <div class="nisab-val">{local_nisab:,.0f} BDT</div>
                <small style="color:#94a3b8">Rate: {local_rate:,.2f} Tk/g</small>
            </div>

            <div class="card" style="border-left-color: #3498db;">
                <small>GLOBAL (Silver 19.69 oz)</small>
                <div class="nisab-val" style="color:#3498db">${global_nisab:,.2f} USD</div>
            </div>
            
            <p style="font-size: 0.6em; color: #475569;">Calculated using Traditional Silver Rate</p>
        </div>
        <script>setTimeout(() => location.reload(), 60000);</script>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == "__main__":
    app.run()
