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

def get_data():
    results = {'local_price': 0.00, 'global_price': 0.00}
    
    # --- BAJUS (Local Bangladesh) ---
    try:
        url = "https://bajus.org/gold-price"
        # More realistic headers to avoid being blocked by BAJUS
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                text_content = row.get_text().lower()
                # BAJUS sometimes changes text; looking for silver + traditional
                if 'silver' in text_content and 'traditional' in text_content:
                    cells = row.find_all('td')
                    if cells:
                        raw_price = cells[-1].get_text(strip=True)
                        # Extract only numbers and decimals
                        clean_price = re.sub(r'[^\d.]', '', raw_price)
                        results['local_price'] = float(clean_price)
                        break
    except Exception as e:
        print(f"Local Error: {e}")

    # --- Yahoo Finance (Global USA) ---
    try:
        # Using a more direct method for yfinance in serverless
        silver = yf.Ticker("SI=F")
        data = silver.fast_info
        results['global_price'] = data.last_price
    except Exception as e:
        try:
            # Fallback if fast_info fails
            data = silver.history(period="1d")
            if not data.empty:
                results['global_price'] = data['Close'].iloc[-1]
        except:
            print(f"Global Error: {e}")

    return results

@app.route('/')
def index():
    data = get_data()
    
    local_price = data.get('local_price') or 0.00
    global_price = data.get('global_price') or 0.00
    
    local_nisab = local_price * NISAB_GRAMS
    global_nisab = global_price * NISAB_OZ
    
    current_time = time.strftime('%I:%M:%S %p | %b %d, %Y')

    # Note: Use double curly braces {{ }} for CSS/JS so Python f-strings don't get confused
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zakat Nisab Monitor</title>
        <style>
            :root {{
                --bg-color: #0f172a;
                --card-bg: rgba(255, 255, 255, 0.05);
                --text-main: #ffffff;
                --text-muted: #94a3b8;
                --border-color: rgba(255, 255, 255, 0.1);
                --accent-local: #2ecc71;
                --accent-global: #3498db;
            }}
            [data-theme="light"] {{
                --bg-color: #f1f5f9;
                --card-bg: rgba(255, 255, 255, 0.7);
                --text-main: #1e293b;
                --text-muted: #64748b;
                --border-color: rgba(0, 0, 0, 0.1);
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; transition: background 0.3s, color 0.3s; }}
            body {{
                background: var(--bg-color);
                color: var(--text-main);
                font-family: sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 20px;
            }}
            .main-container {{
                width: 100%;
                max-width: 500px;
                background: var(--card-bg);
                backdrop-filter: blur(10px);
                border: 1px solid var(--border-color);
                padding: 30px;
                border-radius: 20px;
                text-align: center;
            }}
            .card {{
                background: rgba(0, 0, 0, 0.1);
                padding: 15px;
                border-radius: 12px;
                margin: 15px 0;
                text-align: left;
                border-left: 5px solid gray;
            }}
            .local {{ border-left-color: var(--accent-local); }}
            .global {{ border-left-color: var(--accent-global); }}
            .nisab-val {{ font-size: 1.8rem; font-weight: bold; margin-top: 5px; color: var(--text-main); }}
            .local .nisab-val {{ color: var(--accent-local); }}
            .global .nisab-val {{ color: var(--accent-global); }}
            .timestamp {{ font-size: 0.8rem; color: var(--text-muted); }}
            .theme-toggle {{ position: fixed; top: 10px; right: 10px; padding: 8px 15px; cursor: pointer; border-radius: 20px; border: 1px solid var(--border-color); background: var(--card-bg); color: var(--text-main); }}
        </style>
    </head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">🌙 Mode</button>
        <div class="main-container">
            <h1>Zakat Nisab Monitor</h1>
            <p class="timestamp">{current_time}</p>
            
            <div class="card local">
                <small>BD (BAJUS) - 1g Silver</small>
                <div>{local_price:,.2f} BDT</div>
                <hr style="margin: 10px 0; opacity: 0.1;">
                <small>Nisab Threshold (612.35g):</small>
                <div class="nisab-val">{local_nisab:,.2f} BDT</div>
            </div>

            <div class="card global">
                <small>Global - 1oz Silver</small>
                <div>${global_price:,.2f} USD</div>
                <hr style="margin: 10px 0; opacity: 0.1;">
                <small>Nisab Threshold (19.69oz):</small>
                <div class="nisab-val">${global_nisab:,.2f} USD</div>
            </div>
            
            <div style="font-size: 0.8rem; color: var(--text-muted); text-align: left; margin-top: 20px;">
                <strong>Note:</strong> Nisab is 52.5 Tola silver. If you hold this value for one lunar year, 2.5% Zakat is due.
            </div>
        </div>

        <script>
            function toggleTheme() {{
                const body = document.body;
                if (body.getAttribute('data-theme') === 'light') {{
                    body.removeAttribute('data-theme');
                    localStorage.setItem('theme', 'dark');
                }} else {{
                    body.setAttribute('data-theme', 'light');
                    localStorage.setItem('theme', 'light');
                }}
            }}
            if (localStorage.getItem('theme') === 'light') {{
                document.body.setAttribute('data-theme', 'light');
            }}
            setTimeout(() => location.reload(), 60000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

app = app
