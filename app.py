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

def get_bajus_silver():
    """Extracts Traditional Silver price from BAJUS."""
    # March 2026 standard for Traditional Silver is ~BDT 345-450 per gram
    url = "https://bajus.org/gold-price"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, "Blocked"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            text = row.get_text().lower()
            
            # Target 'Silver' and 'Traditional' (Sonatan)
            if 'silver' in text and ('traditional' in text or 'সনাতন' in text):
                # BAJUS now lists Per Gram and Per Bhori. We want Per Gram.
                # If the cell looks like a small number (345), it's Gram. 
                # If it's large (4024), it's Bhori.
                for cell in reversed(cells):
                    val_text = re.sub(r'[^\d.]', '', cell.get_text())
                    if val_text:
                        val = float(val_text)
                        # If value > 1000, it's bhori price; convert to gram
                        if val > 1000:
                            return val / 11.664, "Live"
                        else:
                            return val, "Live"
    except Exception as e:
        print(f"Scrape Error: {e}")
    return None, "Failed"

@app.route('/')
def index():
    # 1. Get Local Data
    local_gram_price, status = get_bajus_silver()
    
    # Backup: Last known March 2026 price if scraping is blocked
    if not local_gram_price:
        local_gram_price = 345.0  # Last known rate per gram
        status = "Offline (Showing Last Known)"

    # 2. Get Global Data
    global_oz_price = 0.0
    try:
        silver = yf.Ticker("SI=F")
        hist = silver.history(period="1d")
        if not hist.empty:
            global_oz_price = hist['Close'].iloc[-1]
    except:
        pass

    local_nisab = local_gram_price * NISAB_GRAMS
    global_nisab = global_oz_price * NISAB_OZ
    current_time = time.strftime('%I:%M %p | %b %d, %Y')

    # Color logic for status
    status_color = "#2ecc71" if "Live" in status else "#e74c3c"

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zakat Monitor BD</title>
        <style>
            body {{ background: #0f172a; color: white; font-family: 'Segoe UI', sans-serif; display: flex; flex
