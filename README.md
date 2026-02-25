# Precios Dólar Futuro - tradermarket.com.ar

Este repositorio contiene el script encargado de obtener los precios del **Dólar Futuro** desde Matba Rofex (utilizando la librería `pyRofex`) para visualizar la curva de vencimientos en **tradermarket.com.ar**.

## Funcionamiento del Script (`get_prices_once.py`)

1. **Autenticación**: Se conecta a la API de Matba Rofex (entorno REMARKET/Primary API) usando credenciales almacenadas de forma segura (variables de entorno o GitHub Secrets).
2. **Obtención de Tickers**: Busca automáticamente todos los contratos de futuro de dólar válidos (ej. `DLR/ENE25`, `DLR/FEB25`) y los ordena cronológicamente.
3. **Suscripción WebSocket (Tiempo Real)**: Se suscribe por WebSocket a los tickers obtenidos para capturar instantáneamente las puntas de compra (`BID`), venta (`OFFER`) y el último precio operado (`LAST`). Espera 15 segundos acumulando datos.
4. **Respaldo REST (Snapshot)**: Para asegurar disponibilidad de datos incluso con mercado cerrado, si algún ticker no obtuvo su último precio por WebSocket, hace una petición REST secundaria para obtener el último cierre histórico.
5. **Generación de JSON**: Extrae y consolida los datos en el archivo `curva_dlr.json`, incluyendo un timestamp de actualización.

## Automatización con GitHub Actions

El flujo definido en `.github/workflows/update_prices.yml` se encarga de:
- Instalar dependencias necesarias (`pyRofex`, `python-dotenv`).
- Ejecutar el script recurrentemente.
- **Cron**: Configurado para ejecutarse **cada 20 minutos de Lunes a Viernes, en horario de mercado (10:30 a 17:00 ART / 13:30 a 20:00 UTC)**.
- Hacer el `commit` y `push` automático del archivo `curva_dlr.json` al repositorio en caso de cambios.

De esta forma, la página **tradermarket.com.ar** consume el archivo `curva_dlr.json` siempre actualizado para renderizar los gráficos de la curva de Rofex sin necesidad de mantener un servidor dedicado.
