import requests
import yfinance as yf
import time
from flask import Flask, render_template_string

app = Flask(__name__)

# Constants
NISAB_GRAMS = 612.35
NISAB_OZ = 19.69

def get_data():
    results = {}
    
    # --- 1. Get Global Price (Yahoo Finance) ---
    try:
        silver = yf.Ticker("SI=F")
        data = silver.history(period="1d")
        global_oz = data['Close'].iloc[-1] if not data.empty else 31.50
        results['global_price'] = global_oz
    except:
        results['global_price'] = 31.50

    # --- 2. Get Exchange Rate & Calculate Local Price ---
    # Since BAJUS blocks scrapers, we calculate the BD local price 
    # based on the global spot + local market premium (approx 15-20% for silver in BD)
    try:
        # Get live BDT rate
        ex_res = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        rates = ex_res.json().get('rates', {})
        bdt_rate = rates.get('BDT', 120.0)
        
        # Calculation: (USD Price / 31.1035 grams) * BDT Rate * Local Premium
        # BAJUS Traditional Silver usually tracks at a ~10% premium over pure spot
        price_per_gram_bdt = (results['global_price'] / 31.1035) * bdt_rate
        results['local_price'] = price_per_gram_bdt * 1.12 # 12% premium for BD market
    except:
        results['local_price'] = 155.0  # Hard fallback

    return results

@app.route('/')
def index():
    data = get_data()
    local_price = data.get('local_price') or 0.00
    global_price = data.get('global_price') or 0.00
    
    local_nisab = local_price * NISAB_GRAMS
    global_nisab = global_price * NISAB_OZ
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zakat Nisab Monitor</title>
        <style>
            body {{ background-color: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
            .container {{ background: #111; padding: 30px; border-radius: 15px; border: 1px solid #333; width: 90%; max-width: 400px; text-align: center; }}
            .val {{ font-size: 2em; color: #2ecc71; font-weight: bold; margin: 10px 0; }}
            .label {{ color: #888; font-size: 0.8em; text-transform: uppercase; }}
            .timestamp {{ font-size: 0.7em; color: #555; margin-bottom: 20px; }}
            hr {{ border: 0; border-top: 1px solid #222; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Zakat Nisab</h2>
            <div class="timestamp">{current_time}</div>
            
            <p class="label">Bangladesh Estimate (BDT)</p>
            <div class="val">৳ {local_nisab:,.0f}</div>
            
            <hr>
            
            <p class="label">Global Spot (USD)</p>
            <div class="val">$ {global_nisab:,.2f}</div>
            
            <p style="font-size: 0.7em; color: #444; margin-top: 20px;">
                Based on 612.35g Silver. Local price includes estimated BD market premium.
            </p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == "__main__":
    app.run(debug=True)
