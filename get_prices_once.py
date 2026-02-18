import os
import pyRofex
import time
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

def get_dlr_tickers():
    months_map = {
        'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12
    }
    try:
        instruments = pyRofex.get_all_instruments()
        if instruments['status'] == 'OK':
            all_symbols = [inst['instrumentId']['symbol'] for inst in instruments['instruments']]
            dlr_tickers = [s for s in all_symbols if s.startswith("DLR/") and len(s) == 9 and not s.endswith("A") and not s.endswith("M") and "/" in s and s.count("/") == 1 and " " not in s]
            
            def sort_key(ticker):
                month_str, year_str = ticker[4:7], ticker[7:9]
                return (int(year_str) * 100) + months_map.get(month_str, 0)
            
            return sorted(dlr_tickers, key=sort_key)
    except: return []
    return []

# Captura de datos
current_data = {}

def market_data_handler(message):
    instrumento = message["instrumentId"]["symbol"]
    md = message["marketData"]
    current_data[instrumento] = {
        "bid": md["BI"][0]["price"] if md.get("BI") else "S/D",
        "offer": md["OF"][0]["price"] if md.get("OF") else "S/D",
        "last": md["LA"]["price"] if md.get("LA") and isinstance(md["LA"], dict) else "S/D"
    }

def main():
    try:
        pyRofex.initialize(
            user=os.getenv("PRIMARY_USER"),
            password=os.getenv("PRIMARY_PASSWORD"),
            account=os.getenv("PRIMARY_ACCOUNT"),
            environment=pyRofex.Environment.REMARKET
        )
        
        tickers = get_dlr_tickers()
        if not tickers: return

        pyRofex.init_websocket_connection(market_data_handler=market_data_handler, error_handler=lambda m: None)
        pyRofex.market_data_subscription(tickers=tickers)
        
        time.sleep(10) # Tiempo para capturar datos
        pyRofex.close_websocket_connection()

        output = []
        for t in tickers:
            d = current_data.get(t, {"bid": "S/D", "offer": "S/D", "last": "S/D"})
            output.append({"ticker": t, "bid": d["bid"], "offer": d["offer"], "last": d["last"], "timestamp": datetime.datetime.now().isoformat()})

        with open("curva_dlr.json", "w") as f:
            json.dump(output, f, indent=4)
        print("✅ JSON actualizado con éxito.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
