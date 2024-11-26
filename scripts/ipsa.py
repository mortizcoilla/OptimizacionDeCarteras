import yfinance as yf
import pandas as pd

# Carga tu lista de tickers (puedes reemplazar esta lista con la tuya propia)
tickers = ["SOQUICOM.SN","CHILE.SN","BSANTANDER.SN","CENCOSUD.SN","COPEC.SN","ENELAM.SN","BCI.SN","CMPC.SN","FALABELLA.SN","ENELCHILE.SN",
            "COLBUN.SN","PARAUCO.SN","VAPORES.SN","AGUAS-A.SN","ANDINA-B.SN","CCU.SN","QUINENCO.SN","CENCOMALLS.SN","LTM.SN",
            "CONCHATORO.SN","ENTEL.SN","MALLPLAZA.SN","CAP.SN","ECL.SN","ITAUCL.SN","ORO-BLANCO.SN","IAM.SN","SMU.SN","RIPLEY.SN",
            "SONDA.SN"]

# Lista para almacenar los datos recolectados
data = []

# Recorre cada ticker y descarga la información básica
for ticker_symbol in tickers:
    print(f"Procesando: {ticker_symbol}")
    try:
        # Crea el objeto del ticker
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Agrega la información básica del activo a la lista de datos
        data.append({
            "Ticker": ticker_symbol,
            "Nombre completo": info.get("longName", "No disponible"),
            "Sector": info.get("sector", "No disponible"),
            "Industria": info.get("industry", "No disponible"),
            "Divisa": info.get("currency", "No disponible"),
            "Precio actual": info.get("currentPrice", "No disponible"),
            "Capitalización de mercado": info.get("marketCap", "No disponible"),
            "Beta": info.get("beta", "No disponible"),
            "Rendimiento de dividendos": info.get("dividendYield", "No disponible"),
            "Última fecha de dividendos": info.get("lastDividendDate", "No disponible"),
            "País": info.get("country", "No disponible"),
            "Bolsa": info.get("exchange", "No disponible"),
            "Símbolo en la bolsa": info.get("symbol", "No disponible"),
        })
    except Exception as e:
        print(f"Error procesando {ticker_symbol}: {e}")
        data.append({
            "Ticker": ticker_symbol,
            "Nombre completo": "Error al obtener datos",
            "Sector": "N/A",
            "Industria": "N/A",
            "Divisa": "N/A",
            "Precio actual": "N/A",
            "Capitalización de mercado": "N/A",
            "Beta": "N/A",
            "Rendimiento de dividendos": "N/A",
            "Última fecha de dividendos": "N/A",
            "País": "N/A",
            "Bolsa": "N/A",
            "Símbolo en la bolsa": "N/A",
        })

# Convierte los datos a un DataFrame de pandas
ipsa = pd.DataFrame(data)

# Convierte la columna 'Capitalización de mercado' a numérica, llenando los valores faltantes con 0
ipsa['Capitalización de mercado'] = pd.to_numeric(ipsa['Capitalización de mercado'].fillna(0))

# Guarda los datos en un archivo CSV
output_file = "ipsa.csv"

# Guardar los datos en un archivo CSV
ipsa.to_csv('src/assets/data/ipsa.csv', index=True)
