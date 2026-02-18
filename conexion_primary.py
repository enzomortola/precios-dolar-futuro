import pyRofex

# 1. Configuración de credenciales
# Reemplaza con tus datos de Veta Capital
USER = "TU_USUARIO"
PASSWORD = "TU_PASSWORD"
ACCOUNT = "TU_CUENTA_VETA" # Ej: REC1234
ENVIRONMENT = pyRofex.Environment.REMARKETS  # Cambiar a .LIVE para producción

def conectar():
    try:
        # 2. Inicializar el entorno
        pyRofex.initialize(
            user=USER,
            password=PASSWORD,
            account=ACCOUNT,
            environment=ENVIRONMENT
        )
        print(f"✅ Conexión exitosa al entorno {ENVIRONMENT}")

        # 3. Prueba de conexión: Obtener datos de la cuenta
        account_data = pyRofex.get_account_report()
        
        if account_data['status'] == 'OK':
            print("📊 Reporte de cuenta recibido:")
            print(f"Estado: {account_data['accountData']['state']}")
        else:
            print("❌ Error en el reporte de cuenta:", account_data)

    except Exception as e:
        print(f"⚠️ Error al intentar conectar: {e}")

if __name__ == "__main__":
    conectar()
    
    # Ejemplo: Obtener una cotización rápida (ej: Dólar Matba Rofex o un Bono)
    # ticker = "DLR/ENE26" 
    # market_data = pyRofex.get_market_data(tickers=[ticker], entries=[pyRofex.MarketDataEntry.BIDS, pyRofex.MarketDataEntry.OFFERS])
    # print(market_data)