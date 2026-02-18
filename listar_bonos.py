import os
import pyRofex
import json
from dotenv import load_dotenv

load_dotenv()

def listar_bonos():
    try:
        # Inicializar conexión
        pyRofex.initialize(
            user=os.getenv("PRIMARY_USER"),
            password=os.getenv("PRIMARY_PASSWORD"),
            account=os.getenv("PRIMARY_ACCOUNT"),
            environment=pyRofex.Environment.REMARKET
        )
        print("Obteniendo todos los instrumentos del mercado...")
        
        # Obtener todos los instrumentos
        res = pyRofex.get_all_instruments()
        
        if res['status'] != 'OK':
            print("Error al obtener instrumentos:", res)
            return

        instruments = res['instruments']
        print(f"Total de instrumentos encontrados: {len(instruments)}")
        
        bonos = []
        
        print("\nFiltrando instrumentos de Renta Fija (Bonos comuns)...")
        
        for inst in instruments:
            symbol = inst['instrumentId']['symbol']
            
            # Criterio simple para detectar Bonos:
            # Generalmente tienen números (AL30, GD30, TX24) y NO son futuros de ROFEX o DLR
            # Excluimos DLR, opciones, y futuros de índices
            if (any(c.isdigit() for c in symbol) and 
                not symbol.startswith('DLR') and 
                not symbol.startswith('RFX') and
                len(symbol) < 15): # Evitar nombres muy largos complejos
                
                bonos.append(symbol)

        # Ordenar y mostrar
        bonos_sorted = sorted(bonos)
        
        print(f"\n--- Bonos Detectados ({len(bonos_sorted)}) ---")
        for i, bono in enumerate(bonos_sorted):
            print(f"{i+1}. {bono}")
            
        # Opcional: Guardar en archivo
        with open("lista_bonos.txt", "w") as f:
            for b in bonos_sorted:
                f.write(f"{b}\n")
        print("\nLista guardada en 'lista_bonos.txt'")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    listar_bonos()
