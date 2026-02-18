import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import pyRofex
from dotenv import load_dotenv
from simulator import Portfolio
from collections import defaultdict

# Cargar variables
load_dotenv()

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💰 Simulador de Trading Pro - Matba Rofex")
        self.root.geometry("1000x700")
        
        # Estilos
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Datos del Modelo
        self.portfolio = Portfolio()
        self.current_category = tk.StringVar()
        self.current_ticker = tk.StringVar()
        self.market_data = {} # {ticker: {bid: ..., offer: ..., last: ...}}
        self.all_instruments = defaultdict(list)
        self.connected = False
        self.subscribed_ticker = None
        
        # Layout Principal
        self.create_header()
        self.create_main_area()
        self.create_footer()
        
        # Iniciar Thread de Conexion y Carga
        self.start_backend_thread()
        
        # Loop de Actualización GUI
        self.root.after(1000, self.update_ui)

    def create_header(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.X)
        
        ttk.Label(frame, text="Broker Ficticio Pro", font=("Arial", 18, "bold")).pack(side=tk.LEFT)
        
        self.lbl_balance = ttk.Label(frame, text=f"Saldo Liquido: ${self.portfolio.cash:,.2f}", font=("Arial", 14, "bold"), foreground="green")
        self.lbl_balance.pack(side=tk.RIGHT)
        
        self.lbl_status = ttk.Label(frame, text="⏳ Conectando...", foreground="orange")
        self.lbl_status.pack(side=tk.RIGHT, padx=20)

    def create_main_area(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Panel Izquierdo: Mercado e Instrumentos ---
        left_panel = ttk.LabelFrame(main_frame, text="Panel de Mercado", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Categorias
        ttk.Label(left_panel, text="1. Categoría:").pack(anchor=tk.W)
        self.cb_category = ttk.Combobox(left_panel, textvariable=self.current_category, state="readonly")
        self.cb_category.pack(fill=tk.X, pady=5)
        self.cb_category.bind("<<ComboboxSelected>>", self.on_category_change)
        
        # Selector de Ticker con búsqueda
        ttk.Label(left_panel, text="2. Ticker (Escribe para filtrar):").pack(anchor=tk.W, pady=(10, 0))
        self.ent_search = ttk.Entry(left_panel)
        self.ent_search.pack(fill=tk.X, pady=2)
        self.ent_search.bind("<KeyRelease>", self.filter_tickers)
        
        self.cb_ticker = ttk.Combobox(left_panel, textvariable=self.current_ticker, state="readonly")
        self.cb_ticker.pack(fill=tk.X, pady=5)
        self.cb_ticker.bind("<<ComboboxSelected>>", self.on_ticker_change)
        
        # Precios Grandes
        price_display = ttk.Frame(left_panel, padding="20", relief="groove")
        price_display.pack(fill=tk.X, pady=15)
        
        self.lbl_ticker_name = ttk.Label(price_display, text="Seleccione un activo", font=("Arial", 12, "italic"))
        self.lbl_ticker_name.pack(pady=5)

        self.lbl_bid = ttk.Label(price_display, text="COMPRA: -", font=("Arial", 14), foreground="blue")
        self.lbl_bid.pack(anchor=tk.W, pady=2)
        
        self.lbl_ask = ttk.Label(price_display, text="VENTA: -", font=("Arial", 14), foreground="red")
        self.lbl_ask.pack(anchor=tk.W, pady=2)
        
        self.lbl_last = ttk.Label(price_display, text="ÚLTIMO: -", font=("Arial", 20, "bold"))
        self.lbl_last.pack(anchor=tk.W, pady=10)

        # Panel de Operacion
        op_frame = ttk.LabelFrame(left_panel, text="Operar", padding="10")
        op_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(op_frame, text="Cantidad:").grid(row=0, column=0, padx=5)
        self.ent_qty = ttk.Entry(op_frame, width=15)
        self.ent_qty.insert(0, "1")
        self.ent_qty.grid(row=0, column=1, padx=5)
        
        btn_buy = tk.Button(op_frame, text="COMPRAR 📈", bg="#90ee90", font=("Arial", 10, "bold"), command=self.buy_action)
        btn_buy.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        
        btn_sell = tk.Button(op_frame, text="VENDER 📉", bg="#ffcccb", font=("Arial", 10, "bold"), command=self.sell_action)
        btn_sell.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        # --- Panel Derecho: Portafolio ---
        right_panel = ttk.LabelFrame(main_frame, text="Mi Portafolio", padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        cols = ("Ticker", "Cantidad", "Val. Mercado", "Total")
        self.tree = ttk.Treeview(right_panel, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def create_footer(self):
        self.txt_log = tk.Text(self.root, height=6, state="disabled", bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.txt_log.pack(fill=tk.X, padx=10, pady=5)

    def log(self, msg):
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")

    # --- Backend Threading ---
    def start_backend_thread(self):
        t = threading.Thread(target=self.run_backend, daemon=True)
        t.start()
    
    def run_backend(self):
        try:
            self.log("Conectando a Primary Remarket...")
            pyRofex.initialize(
                user=os.getenv("PRIMARY_USER"),
                password=os.getenv("PRIMARY_PASSWORD"),
                account=os.getenv("PRIMARY_ACCOUNT"),
                environment=pyRofex.Environment.REMARKET
            )
            self.connected = True
            self.log("✅ Conexión establecida.")

            # Cargar Instrumentos
            self.log("Cargando listado de instrumentos...")
            res = pyRofex.get_all_instruments()
            if res['status'] == 'OK':
                self.categorize_instruments(res['instruments'])
                self.log(f"✅ {len(res['instruments'])} instrumentos cargados.")
                self.root.after(0, self.setup_categories)
            
            # WebSocket Handler
            def md_handler(msg):
                ticker = msg["instrumentId"]["symbol"]
                md = msg["marketData"]
                bid = md["BI"][0]["price"] if md.get("BI") else None
                offer = md["OF"][0]["price"] if md.get("OF") else None
                last = md["LA"]["price"] if md.get("LA") else None
                self.market_data[ticker] = {"bid": bid, "offer": offer, "last": last}

            pyRofex.init_websocket_connection(market_data_handler=md_handler)
            
        except Exception as e:
            self.connected = False
            self.log(f"❌ Error Backend: {e}")

    def categorize_instruments(self, instruments):
        for inst in instruments:
            symbol = inst['instrumentId']['symbol']
            # Lógica de categorización refinada
            if symbol.startswith('DLR/'):
                cat = "Dólar Futuro"
            elif '/' in symbol:
                if any(x in symbol for x in ['ORO', 'WTI', 'SOJ', 'MAI', 'TRI']):
                    cat = "Commodities (Futuros)"
                elif ' RFX20' in symbol or ' rfx20' in symbol:
                    cat = "Índices (Futuros)"
                elif ' C ' in symbol or ' P ' in symbol or symbol.startswith('O'):
                    cat = "Opciones"
                else:
                    cat = "Otros Futuros"
            elif any(c.isdigit() for c in symbol) and not symbol.startswith('RFX'):
                cat = "Bonos / TVPP"
            elif 'MERV - XMEV -' in symbol:
                if ' - CI' in symbol or ' - 24hs' in symbol:
                    # Intentar detectar Cedears vs Acciones (simplificado)
                    if any(ced in symbol for ced in ['AAPL', 'TSLA', 'AMZN', 'BABA', 'KO']):
                        cat = "CEDEARs"
                    else:
                        cat = "Acciones"
                else:
                    cat = "Acciones/Otros"
            else:
                cat = "Otros"
            
            self.all_instruments[cat].append(symbol)
        
        # Sort each list
        for cat in self.all_instruments:
            self.all_instruments[cat].sort()

    def setup_categories(self):
        cats = sorted(list(self.all_instruments.keys()))
        self.cb_category['values'] = cats
        if "Acciones" in cats: self.cb_category.set("Acciones")
        elif cats: self.cb_category.set(cats[0])
        self.on_category_change(None)

    # --- Events ---
    def on_category_change(self, event):
        cat = self.current_category.get()
        tickers = self.all_instruments.get(cat, [])
        self.cb_ticker['values'] = tickers
        if tickers:
            self.cb_ticker.set(tickers[0])
            self.on_ticker_change(None)
        else:
            self.cb_ticker.set("")

    def filter_tickers(self, event):
        search = self.ent_search.get().upper()
        cat = self.current_category.get()
        all_in_cat = self.all_instruments.get(cat, [])
        filtered = [t for t in all_in_cat if search in t.upper()]
        self.cb_ticker['values'] = filtered
        if filtered:
            # No cambiamos el set a menos que no haya nada seleccionado o el actual no este en la lista
            if self.cb_ticker.get() not in filtered:
                self.cb_ticker.set(filtered[0])
                self.on_ticker_change(None)

    def on_ticker_change(self, event):
        ticker = self.current_ticker.get()
        if not ticker: return
        
        self.lbl_ticker_name.config(text=ticker)
        
        # Cambiar suscripcion WebSocket
        if self.connected:
            if self.subscribed_ticker and self.subscribed_ticker != ticker:
                # Nota: pyRofex no tiene "unsubscribe" directo facil en esta lib sin cerrar, 
                # pero podemos simplemente suscribir al nuevo. El handler filtrará.
                pass
            
            self.log(f"Suscribiendo a {ticker}...")
            try:
                pyRofex.market_data_subscription(
                    tickers=[ticker],
                    entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS, pyRofex.MarketDataEntry.LAST]
                )
                self.subscribed_ticker = ticker
            except Exception as e:
                self.log(f"Error sub: {e}")

    def update_ui(self):
        # Actualizar Status
        if self.connected:
            self.lbl_status.config(text="✅ Online (Remarket)", foreground="green")
        else:
            self.lbl_status.config(text="❌ Offline", foreground="red")
        
        # Precios
        ticker = self.current_ticker.get()
        data = self.market_data.get(ticker, {})
        self.lbl_bid.config(text=f"COMPRA (Bid): ${data.get('bid', '-'):}")
        self.lbl_ask.config(text=f"VENTA (Ask): ${data.get('offer', '-'):}")
        self.lbl_last.config(text=f"ÚLTIMO: ${data.get('last', '-'):}")
        
        # Actualizar Tabla Portafolio
        self.update_portfolio_table()
        
        self.root.after(500, self.update_ui)

    def update_portfolio_table(self):
        # Limpiar y recargar (optimizable pero simple para este volumen)
        current_items = {self.tree.set(k, "Ticker"): k for k in self.tree.get_children()}
        
        for ticker, qty in self.portfolio.positions.items():
            md = self.market_data.get(ticker, {})
            last_price = md.get('last', 0)
            total = qty * (last_price if last_price else 0)
            
            vals = (ticker, qty, f"${last_price:,.2f}" if last_price else "S/D", f"${total:,.2f}")
            
            if ticker in current_items:
                self.tree.item(current_items[ticker], values=vals)
                del current_items[ticker]
            else:
                self.tree.insert("", "end", values=vals)
        
        # Borrar los que ya no están
        for k in current_items.values():
            self.tree.delete(k)
            
        self.lbl_balance.config(text=f"Saldo Liquido: ${self.portfolio.cash:,.2f}")

    def buy_action(self):
        ticker = self.current_ticker.get()
        if not ticker: return
        try:
            qty = int(self.ent_qty.get())
            if qty <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad inválida")
            return
            
        data = self.market_data.get(ticker)
        if not data or not data.get("offer"):
            # Si el mercado está cerrado, preguntar si quiere simular un precio
            if messagebox.askyesno("Mercado Cerrado", f"No hay precio de venta para {ticker}.\n¿Desea simular una compra a $100.00 para probar?"):
                price = 100.0
            else:
                return
        else:
            price = data["offer"]
            
        success, msg = self.portfolio.buy(ticker, qty, price)
        if success:
            self.log(f"ORDEN EXITOSA: {msg}")
            # Actualizar tabla inmediatamente
            self.update_portfolio_table()
        else:
            messagebox.showwarning("Orden Rechazada", msg)

    def sell_action(self):
        ticker = self.current_ticker.get()
        if not ticker: return
        try:
            qty = int(self.ent_qty.get())
            if qty <= 0: raise ValueError
        except:
            messagebox.showerror("Error", "Cantidad inválida")
            return

        if ticker not in self.portfolio.positions:
            messagebox.showerror("Error", "No tienes este activo en cartera.")
            return

        data = self.market_data.get(ticker)
        if not data or not data.get("bid"):
            if messagebox.askyesno("Mercado Cerrado", f"No hay precio de compra para {ticker}.\n¿Desea simular una venta a $105.00 para probar?"):
                price = 105.0
            else:
                return
        else:
            price = data["bid"]

        success, msg = self.portfolio.sell(ticker, qty, price)
        if success:
            self.log(f"ORDEN EXITOSA: {msg}")
            self.update_portfolio_table()
        else:
            messagebox.showwarning("Orden Rechazada", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
