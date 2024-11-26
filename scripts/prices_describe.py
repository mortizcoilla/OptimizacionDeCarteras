# Carga de Librerias

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from pypfopt import EfficientFrontier, objective_functions
from pypfopt import risk_models
from pypfopt import expected_returns
import cvxpy as cp
from scipy.optimize import minimize

# Lista de tickers de las empresas IPSA

tickers =  ["SOQUICOM.SN","CHILE.SN","BSANTANDER.SN","CENCOSUD.SN","COPEC.SN","ENELAM.SN","BCI.SN","CMPC.SN","FALABELLA.SN","ENELCHILE.SN",
            "COLBUN.SN","PARAUCO.SN","VAPORES.SN","AGUAS-A.SN","ANDINA-B.SN","CCU.SN","QUINENCO.SN","CENCOMALLS.SN","LTM.SN",
            "CONCHATORO.SN","ENTEL.SN","MALLPLAZA.SN","CAP.SN","ECL.SN","ITAUCL.SN","ORO-BLANCO.SN","IAM.SN","SMU.SN","RIPLEY.SN",
            "SONDA.SN"]

# Definimos la fecha de inicio y fin para los últimos 5 años
end_date = pd.Timestamp.today()
start_date = end_date - pd.DateOffset(years=5)

# Descargamos los datos
data = yf.download(tickers, start=start_date, end=end_date, interval="1wk")

# Seleccionamos solo el 'Adj Close' y creamos una copia para trabajar en ella
prices = data['Adj Close'].copy()

# 1. Manejo de datos faltantes
missing_data = prices.isnull().sum()
print(f"Datos faltantes por ticker antes de la limpieza:\n{missing_data}\n")

# 2. Verificar valores duplicados
duplicates = prices[prices.index.duplicated()]
if len(duplicates) == 0:
    print("No hay valores duplicados.\n")
else:
    print(f"Valores duplicados encontrados:\n{duplicates}\n")
    prices.drop_duplicates(inplace=True)

# 3. Ordenar datos por fecha
prices.sort_index(inplace=True)

# 4. Verificar la existencia de outliers
for ticker in tickers:
    mean, std = prices[ticker].mean(), prices[ticker].std()
    outliers = prices[(prices[ticker] < mean - 3 * std) | (prices[ticker] > mean + 3 * std)][ticker]
    if not outliers.empty:
        print(f"Outliers detectados en {ticker}:\n{outliers}\n")

# 5. Llenar datos faltantes usando 'ffill' directamente
prices.ffill(inplace=True)

# Verificar si todavía hay datos faltantes
missing_data_after = prices.isnull().sum()
print(f"Datos faltantes por ticker después de la limpieza:\n{missing_data_after}\n")

# Describir estadísticos de los precios
describe_stats = prices.describe()
print(describe_stats)

# Guardar el resumen estadístico en un archivo CSV
describe_stats.to_csv('src/assets/data/prices_describe.csv', index=True)
