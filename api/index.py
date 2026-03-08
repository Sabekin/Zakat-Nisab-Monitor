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
    results = {}
    # --- BAJUS (Local Bangladesh) ---
    try:
        url = "https://bajus.org/gold-price"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all('tr')
        for row in rows:
            text_content = row.get_text().lower()
            if 'silver' in text_content and 'traditional' in text_content:
                cells = row.find_all('td')
                raw_price = cells[-1].get_text(strip=True)
                results['local_price'] = float(re.sub(r'[^\d.]', '', raw_price))
                break
    except:
        results['local_price'] = None

    # --- Yahoo Finance (Global USA) ---
    try:
        silver = yf.Ticker("SI=F")
        data = silver.history(period="1d")
        results['global_price'] = data['Close'].iloc[-1] if not data.empty else 0.00
    except:
        results['global_price'] = None

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
                background-image: radial-gradient(circle at 50% 50%, rgba(52, 152, 219, 0.1) 0%, transparent 50%);
                color: var(--text-main);
                font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }}

            .theme-toggle {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 18px;
                border-radius: 30px;
                border: 1px solid var(--border-color);
                background: var(--card-bg);
                color: var(--text-main);
                backdrop-filter: blur(10px);
                cursor: pointer;
                font-size: 0.9em;
                font-weight: 600;
                z-index: 1000;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}

            .main-container {{
                width: 100%;
                max-width: 500px;
                background: var(--card-bg);
                backdrop-filter: blur(16px) saturate(180%);
                -webkit-backdrop-filter: blur(16px) saturate(180%);
                border: 1px solid var(--border-color);
                padding: 35px;
                border-radius: 24px;
                text-align: center;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
            }}

            h1 {{ font-weight: 700; letter-spacing: -0.5px; margin-bottom: 5px; }}
            .timestamp {{ font-size: 0.85em; color: var(--text-muted); margin-bottom: 30px; }}

            .card {{
                background: rgba(0, 0, 0, 0.05);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 20px;
                text-align: left;
            }}
            .card.local {{ border-left: 5px solid var(--accent-local); }}
            .card.global {{ border-left: 5px solid var(--accent-global); }}

            .label {{ color: var(--text-muted); font-size: 0.75em; text-transform: uppercase; font-weight: bold; }}
            .price-val {{ font-weight: 600; font-size: 1.3em; margin-bottom: 12px; }}
            .nisab-box {{ margin-top: 10px; border-top: 1px solid var(--border-color); padding-top: 12px; }}
            .nisab-title {{ font-size: 0.85em; color: var(--text-muted); margin-bottom: 4px; }}
            .nisab-val {{ font-size: 2.2em; font-weight: 800; font-family: 'Courier New', monospace; }}
            
            .local .nisab-val {{ color: var(--accent-local); }}
            .global .nisab-val {{ color: var(--accent-global); }}
            
            .notes-section {{
                margin-top: 25px;
                padding-top: 20px;
                border-top: 1px solid var(--border-color);
                text-align: left;
                font-size: 0.85em;
                color: var(--text-muted);
                line-height: 1.6;
            }}
            .notes-header {{ color: var(--text-main); font-weight: bold; margin-bottom: 5px; }}
            
            .footer {{
                margin-top: 30px;
                font-size: 0.75em;
                color: var(--text-muted);
                text-align: center;
                max-width: 500px;
            }}
        </style>
    </head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">🌙 Mode</button>

        <div class="main-container">
            <h1>Zakat Nisab Monitor</h1>
            <p class="timestamp">{current_time}</p>
            
            <div class="card local">
                <p class="label">Bangladesh (BAJUS) - 1g Silver</p>
                <p class="price-val">{local_price:,.2f} BDT</p>
                <div class="nisab-box">
                    <p class="nisab-title">Nisab Threshold (612.35g):</p>
                    <div class="nisab-val">{local_nisab:,.2f} BDT</div>
                </div>
            </div>

            <div class="card global">
                <p class="label">Global (USA) - 1oz Silver</p>
                <p class="price-val">${global_price:,.2f} USD</p>
                <div class="nisab-box">
                    <p class="nisab-title">Nisab Threshold (19.69oz):</p>
                    <div class="nisab-val">${global_nisab:,.2f} USD</div>
                </div>
            </div>

            <div class="notes-section">
                <p class="notes-header">Note:</p>
                <p>Nisab Weight: 52.5 Tola = 612.35 Grams = 19.69 Troy Oz</p>
                <p style="margin-top: 8px;">If your net assets exceed this amount for one lunar year, you are required to pay 2.5% of those assets as Zakat.</p>
            </div>
        </div>

        <div class="footer">
            &copy; 2026 Sabekin Muhammad | Support via bKash/Nagad/Rocket: +8801632407482
        </div>

        <script>
            function toggleTheme() {{
                const body = document.body;
                const btn = document.getElementById('themeBtn');
                if (body.getAttribute('data-theme') === 'light') {{
                    body.removeAttribute('data-theme');
                    btn.innerHTML = '☀️ Mode';
                    localStorage.setItem('theme', 'dark');
                }} else {{
                    body.setAttribute('data-theme', 'light');
                    btn.innerHTML = '🌙 Mode';
                    localStorage.setItem('theme', 'light');
                }}
            }}

            if (localStorage.getItem('theme') === 'light') {{
                document.body.setAttribute('data-theme', 'light');
                document.getElementById('themeBtn').innerHTML = '🌙 Mode';
            }} else {{
                document.getElementById('themeBtn').innerHTML = '☀️ Mode';
            }}

            setTimeout(function() {{
                window.location.reload();
            }}, 60000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

# For Vercel, the app must be accessible at the top level of the module
app = app
