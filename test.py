def buscar_mercados_y_bonos():
    try:
        # Traemos la lista completa de instrumentos
        all_ins = pyRofex.get_all_instruments()
        
        if all_ins['status'] == 'OK':
            instrumentos = all_ins['instruments']
            
            # Filtramos para ver qué mercados (marketId) existen en tu cuenta
            mercados = set([i['instrumentId']['marketId'] for i in instrumentos])
            print(f"📡 Mercados detectados en esta cuenta: {mercados}")
            
            # Buscamos si hay algo que diga 'AL30' o 'BYMA'
            byma_items = [i['instrumentId']['symbol'] for i in instrumentos if 'BYMA' in i['instrumentId']['marketId']]
            
            if byma_items:
                print(f"✅ ¡Éxito! Se encontraron {len(byma_items)} instrumentos de BYMA.")
                print(f"Ejemplos: {byma_items[:5]}")
            else:
                print("❌ Este entorno de Remarket no tiene habilitado BYMA.")
        else:
            print("No se pudo obtener la lista de instrumentos.")
            
    except Exception as e:
        print(f"Error al buscar: {e}")