import os
import json
import time
import pyRofex
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

PORTFOLIO_FILE = "portfolio.json"

class Portfolio:
    def __init__(self):
        self.cash = 0
        self.positions = {}
        self.load()

    def load(self):
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r") as f:
                    data = json.load(f)
                    self.cash = data.get("cash", 0)
                    self.positions = data.get("positions", {})
            except Exception as e:
                print(f"⚠️ Error cargando portafolio: {e}")
                self.cash = 0
                self.positions = {}
        else:
            print("⚠️ No se encontró portafolio, iniciando vacío.")
            self.cash = 0
            self.positions = {}

    def save(self):
        with open(PORTFOLIO_FILE, "w") as f:
            json.dump({
                "cash": self.cash,
                "positions": self.positions
            }, f, indent=4)

    def buy(self, ticker, qty, price):
        total_cost = qty * price
        if total_cost > self.cash:
            return False, "Saldo insuficiente"
        
        self.cash -= total_cost
        
        # Actualizar posiciones: guardar precio promedio ponderado (PPP) si se desea, 
        # pero por simplicidad sumamos cantidad.
        current_qty = self.positions.get(ticker, 0)
        self.positions[ticker] = current_qty + qty
        
        self.save()
        return True, f"Compra exitosa: {qty} x {ticker} @ ${price}"

    def sell(self, ticker, qty, price):
        current_qty = self.positions.get(ticker, 0)
        if qty > current_qty:
            return False, "Cantidad insuficiente en cartera"
        
        total_income = qty * price
        self.cash += total_income
        
        new_qty = current_qty - qty
        if new_qty == 0:
            del self.positions[ticker]
        else:
            self.positions[ticker] = new_qty
            
        self.save()
        return True, f"Venta exitosa: {qty} x {ticker} @ ${price}"

class Market:
    def __init__(self):
        self.connected = False
        self.connect()

    def connect(self):
        try:
            pyRofex.initialize(
                user=os.getenv("PRIMARY_USER"),
                password=os.getenv("PRIMARY_PASSWORD"),
                account=os.getenv("PRIMARY_ACCOUNT"),
                environment=pyRofex.Environment.REMARKET
            )
            self.connected = True
        except Exception as e:
            print(f"❌ Error conectando a Mercado: {e}")
            self.connected = False

    def get_market_data(self, ticker):
        if not self.connected: 
            return None
        
        try:
            # Solicitamos BI (Bid), OF (Offer), LA (Last)
            # Nota: pyRofex.get_market_data returns a response with status and marketData
            md = pyRofex.get_market_data(
                tickers=[ticker],
                entries=[
                    pyRofex.MarketDataEntry.BIDS,
                    pyRofex.MarketDataEntry.OFFERS,
                    pyRofex.MarketDataEntry.LAST
                ]
            )
            
            if md["status"] == "OK":
                data = md["marketData"][0] # Primer instrumento
                
                bid = data["BI"][0]["price"] if data.get("BI") else None
                offer = data["OF"][0]["price"] if data.get("OF") else None
                last = data["LA"]["price"] if data.get("LA") else None
                
                return {"symbol": ticker, "bid": bid, "offer": offer, "last": last}
            else:
                return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    portfolio = Portfolio()
    market = Market()

    while True:
        clear_screen()
        print("="*40)
        print("   🏦  SIMULADOR DE TRADING - MENU   ")
        print("="*40)
        print(f"💰 Saldo Liquido: ${portfolio.cash:,.2f}")
        
        # Valorizacion rapida (aprox con ultimo precio conocido o 0)
        print("-" * 40)
        print("📂 Tenencias:")
        if not portfolio.positions:
            print("   (Cartera Vacia)")
        else:
            for ticker, qty in portfolio.positions.items():
                print(f"   - {ticker}: {qty} nominales")
        
        print("-" * 40)
        print("1. Consultar Precio (Cotizacion)")
        print("2. Comprar")
        print("3. Vender")
        print("4. Actualizar/Recargar")
        print("5. Salir")
        
        opcion = input("\n👉 Elige una opcion: ")

        if opcion == "1":
            ticker = input("Ingrese Ticker (ej: DLR/ENE26, AL30/24hs): ").strip()
            print("⏳ Obteniendo datos...")
            data = market.get_market_data(ticker)
            if data:
                print(f"\n📊 {data['symbol']}")
                print(f"   Compra (Bid): {data['bid'] if data['bid'] else 'S/D'}")
                print(f"   Venta (Offer): {data['offer'] if data['offer'] else 'S/D'}")
                print(f"   Ultimo:       {data['last'] if data['last'] else 'S/D'}")
            else:
                print("❌ No se pudo obtener datos o mercado cerrado.")
            input("\nPresiona ENTER para continuar...")

        elif opcion == "2":
            ticker = input("Ticker a COMPRAR: ").strip()
            data = market.get_market_data(ticker)
            if not data or not data['offer']:
                print("❌ No hay oferta activa para comprar a precio de mercado.")
            else:
                price = data['offer']
                print(f"💲 Precio de Compra (Punta Vendedora): ${price}")
                try:
                    qty = int(input("Cantidad a comprar: "))
                    success, msg = portfolio.buy(ticker, qty, price)
                    print(msg)
                except ValueError:
                    print("❌ Cantidad invalida")
            input("\nPresiona ENTER para continuar...")

        elif opcion == "3":
            ticker = input("Ticker a VENDER: ").strip()
            if ticker not in portfolio.positions:
                print("❌ No tienes este activo.")
            else:
                data = market.get_market_data(ticker)
                if not data or not data['bid']:
                    print("❌ No hay demanda activa para vender a precio de mercado.")
                else:
                    price = data['bid']
                    print(f"💲 Precio de Venta (Punta Compradora): ${price}")
                    try:
                        qty = int(input(f"Cantidad a vender (Max {portfolio.positions[ticker]}): "))
                        success, msg = portfolio.sell(ticker, qty, price)
                        print(msg)
                    except ValueError:
                        print("❌ Cantidad invalida")
            input("\nPresiona ENTER para continuar...")

        elif opcion == "4":
            continue

        elif opcion == "5":
            print("👋 Nos vemos!")
            break

if __name__ == "__main__":
    if not os.getenv("PRIMARY_USER"):
        print("⚠️ ALERTA: No se detectaron credenciales en .env")
    main()
