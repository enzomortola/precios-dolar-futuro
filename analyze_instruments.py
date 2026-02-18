import os
import pyRofex
import json
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

def analyze():
    try:
        pyRofex.initialize(
            user=os.getenv("PRIMARY_USER"),
            password=os.getenv("PRIMARY_PASSWORD"),
            account=os.getenv("PRIMARY_ACCOUNT"),
            environment=pyRofex.Environment.REMARKET
        )
        print("Fetching all instruments...")
        res = pyRofex.get_all_instruments()
        
        if res['status'] != 'OK':
            print("Error:", res)
            return

        instruments = res['instruments']
        print(f"Total: {len(instruments)}")
        
        categories = defaultdict(list)
        for inst in instruments:
            # Categorize by prefix or common logic
            # Common symbols: AL30 (Bonos), GGAL (Acciones), DLR (Futuros), etc.
            symbol = inst['instrumentId']['symbol']
            
            if '/' in symbol:
                if symbol.startswith('DLR'):
                    categories['Dólar Futuro'].append(symbol)
                elif symbol.startswith('O'): # Simplified check for options like O-GGAL...
                     categories['Opciones'].append(symbol)
                else:
                    categories['Otros Futuros/Opciones'].append(symbol)
            elif any(c.isdigit() for c in symbol) and not symbol.startswith('RFX'):
                categories['Bonos'].append(symbol)
            else:
                categories['Acciones/CEDEARs'].append(symbol)

        # Print summary
        for cat, items in categories.items():
            print(f"{cat}: {len(items)} items (ej: {items[:5]})")
            
        with open("instruments_cache.json", "w") as f:
            json.dump(categories, f, indent=4)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
