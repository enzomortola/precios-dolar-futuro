import os
import pyRofex
from dotenv import load_dotenv

load_dotenv()

def inicializar():
    try:
        pyRofex.initialize(
            user=os.getenv("PRIMARY_USER"),
            password=os.getenv("PRIMARY_PASSWORD"),
            account=os.getenv("PRIMARY_ACCOUNT"),
            environment=pyRofex.Environment.REMARKET 
        )
        print("✅ Conexión unificada establecida (ROFX + BYMA Emulado)")
        return True
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return False

# Procesador de datos en tiempo real
def market_data_handler(message):
    instrumento = message["instrumentId"]["symbol"]
    market = message["instrumentId"]["marketId"]
    
    # Extraer puntas de forma segura
    md = message["marketData"]
    bid = md["BI"][0]["price"] if md.get("BI") else "S/D"
    offer = md["OF"][0]["price"] if md.get("OF") else "S/D"
    last = md["LA"]["price"] if md.get("LA") and isinstance(md["LA"], dict) else "S/D"

    print(f"⚡ [{market}] {instrumento.ljust(12)} | Compra: {str(bid).ljust(8)} | Venta: {str(offer).ljust(8)} | Último: {last}")

def error_handler(message):
    print(f"❌ Error en el flujo de datos: {message}")

if __name__ == "__main__":
    if inicializar():
        # Definimos los tickers EXACTOS que vimos en tu captura de pantalla
        # Nota: En Remarket usamos estos, en LIVE usaremos los de BYMA real
        tickers_interes = [
            "DLR/NOV26",    # Futuro Dólar (Vigente)
            "GD30D/24hs",   # Bono GD30 (Dólares)
            "AL30D/24hs"    # Bono AL30 (Dólares)
        ]

        # Iniciar WebSocket
        pyRofex.init_websocket_connection(
            market_data_handler=market_data_handler,
            error_handler=error_handler
        )

        # Suscripción masiva
        pyRofex.market_data_subscription(
            tickers=tickers_interes,
            entries=[
                pyRofex.MarketDataEntry.BIDS, 
                pyRofex.MarketDataEntry.OFFERS, 
                pyRofex.MarketDataEntry.LAST
            ]
        )
        
        print(f"📡 Escaneando {len(tickers_interes)} activos... (Esperando datos 3s)\n")
        
        # Esperar unos segundos para recibir datos y luego desconectar
        import time
        time.sleep(3)
        
        pyRofex.close_websocket_connection()
        print("\n✅ Finalizado.")