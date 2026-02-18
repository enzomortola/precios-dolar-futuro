import os
import pyRofex
import time
import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuración
REFRESH_INTERVAL = 60  # 1 minuto

def get_dlr_tickers():
    """Obtiene contratos mensuales de DLR/ ordenados cronológicamente."""
    months_map = {
        'ENE': 1, 'FEB': 2, 'MAR': 3, 'ABR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DIC': 12
    }
    try:
        instruments = pyRofex.get_all_instruments()
        if instruments['status'] == 'OK':
            all_symbols = [inst['instrumentId']['symbol'] for inst in instruments['instruments']]
            
            dlr_tickers = []
            for s in all_symbols:
                # 1. Filtro base: DLR/ y longitud exacta (ej: DLR/NOV26 es 9 caracteres)
                if not s.startswith("DLR/") or len(s) != 9:
                    continue
                
                # 2. Excluir A, M, Spreads (tienen / extra) y Spots
                if s.endswith("A") or s.endswith("M") or s.count("/") > 1 or "SPOT" in s:
                    continue
                
                dlr_tickers.append(s)

            # 3. Función de ordenamiento cronológico
            def sort_key(ticker):
                # Ticker: DLR/MMM YY
                month_str = ticker[4:7]
                year_str = ticker[7:9]
                month_val = months_map.get(month_str, 0)
                year_val = int(year_str) if year_str.isdigit() else 0
                return (year_val * 100) + month_val

            return sorted(dlr_tickers, key=sort_key)
    except Exception as e:
        print(f"❌ Error al obtener instrumentos: {e}")
    return []

# Diccionario global para guardar los datos momentáneamente
current_data = {}

def market_data_handler(message):
    instrumento = message["instrumentId"]["symbol"]
    md = message["marketData"]
    bid = md["BI"][0]["price"] if md.get("BI") else "S/D"
    offer = md["OF"][0]["price"] if md.get("OF") else "S/D"
    last = md["LA"]["price"] if md.get("LA") and isinstance(md["LA"], dict) else "S/D"
    
    current_data[instrumento] = {
        "bid": bid,
        "offer": offer,
        "last": last
    }

def error_handler(message):
    if "don't exist" in str(message):
        pass
    else:
        print(f"❌ Error: {message}")

def iniciar_servicio():
    global current_data
    try:
        pyRofex.initialize(
            user=os.getenv("PRIMARY_USER"),
            password=os.getenv("PRIMARY_PASSWORD"),
            account=os.getenv("PRIMARY_ACCOUNT"),
            environment=pyRofex.Environment.REMARKET
        )
        
        while True:
            ahora = datetime.datetime.now().strftime("%H:%M:%S")
            current_data = {} # Reset data for this snapshot
            
            tickers = get_dlr_tickers()
            
            if not tickers:
                print(f"[{ahora}] ⚠️ No se encontraron contratos vigentes.")
            else:
                pyRofex.init_websocket_connection(
                    market_data_handler=market_data_handler,
                    error_handler=error_handler
                )
                
                pyRofex.market_data_subscription(
                    tickers=tickers,
                    entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
                )
                
                time.sleep(5)
                pyRofex.close_websocket_connection()

                # Imprimir tabla ordenada alfabéticamente e imprimir a JSON
                print(f"\n--- Curva DLR Futuro [{ahora}] ---")
                output_data = []
                for ticker in sorted(tickers, key=sort_key):
                    d = current_data.get(ticker, {"bid": "S/D", "offer": "S/D", "last": "S/D"})
                    print(f"📈 {ticker.ljust(12)} | Compra: {str(d['bid']).ljust(8)} | Venta: {str(d['offer']).ljust(8)} | Último: {str(d['last']).ljust(8)}")
                    output_data.append({
                        "ticker": ticker,
                        "bid": d['bid'],
                        "offer": d['offer'],
                        "last": d['last'],
                        "timestamp": ahora
                    })
                
                # Guardar para integración con otros lenguajes (ej: Java)
                try:
                    import json
                    with open("curva_dlr.json", "w") as f:
                        json.dump(output_data, f, indent=4)
                except Exception as e:
                    print(f"❌ Error al guardar JSON: {e}")
            
            print(f"\nEsperando {REFRESH_INTERVAL}s...")
            time.sleep(REFRESH_INTERVAL - 5)

    except KeyboardInterrupt:
        print("\n🛑 Servicio detenido por el usuario.")
    except Exception as e:
        print(f"⚠️ Error crítico: {e}")

if __name__ == "__main__":
    iniciar_servicio()
